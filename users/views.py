import json
import logging
import os
from django.shortcuts import render, redirect
from django.contrib.auth import logout, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.http import JsonResponse
from forums.models import Forum, Topic, Comment, Tag
from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm

logger = logging.getLogger(__name__)


@login_required
def profile_view(request):
    created_forums = Forum.objects.filter(creator=request.user)
    joined_forums = Forum.objects.filter(members=request.user).exclude(creator=request.user)
    recent_topics = Topic.objects.filter(author=request.user).order_by('-created_at')[:3]
    recent_comments = Comment.objects.filter(author=request.user).order_by('-created_at')[:5]

    context = {
        'created_forums': created_forums,
        'joined_forums': joined_forums,
        'recent_topics': recent_topics,
        'recent_comments': recent_comments,
    }
    return render(request, 'profile.html', context)


@csrf_protect
@login_required
def delete_profile(request):
    if request.method == 'POST':
        user = request.user

        if hasattr(user, 'userprofile') and user.userprofile.profile_pic:
            try:
                profile_pic_path = user.userprofile.profile_pic.path

                if os.path.isfile(profile_pic_path):
                    os.remove(profile_pic_path)
                    logger.info(f"Deleted profile picture for user {user.username}")
            except Exception as e:
                logger.error(f"Error deleting profile picture for user {user.username}: {str(e)}")

        logout(request)
        user.delete()
        return redirect('home')
    return redirect('users:profile')


def settings_view(request):
    current_theme = request.COOKIES.get('theme', 'light')

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if 'theme' in request.GET:
        theme = request.GET.get('theme', 'light')

        if is_ajax:
            response = JsonResponse({'success': True, 'theme': theme})
            response.set_cookie('theme', theme, httponly=True, secure=True, max_age=31536000)
            return response

        response = render(request, 'settings.html', {'current_theme': theme})
        response.set_cookie('theme', theme, httponly=True, secure=True, max_age=31536000)
        return response

    return render(request, 'settings.html', {'current_theme': current_theme})


def logout_view(request):
    logout(request)
    return redirect('home')


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('users:profile')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            request.session.set_expiry(1209600)

            return redirect('users:quiz')
        else:
            if form.non_field_errors():
                for error in form.non_field_errors():
                    messages.error(request, error)

            for field, errors in form.errors.items():
                for error in errors:
                    field_name = form[field].label if field in form.fields else field
                    messages.error(request, f"{error}")
    else:
        form = CustomUserCreationForm()
    return render(request, 'signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('users:profile')

    if request.method == 'GET':
        storage = messages.get_messages(request)
        for message in storage:
            pass
        storage.used = True

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            remember_me = request.POST.get('remember_me', False)
            if remember_me:
                request.session.set_expiry(1209600)
            else:
                request.session.set_expiry(0)

            return redirect('users:profile')
        else:
            if form.non_field_errors():
                for error in form.non_field_errors():
                    messages.error(request, error)

            for field, errors in form.errors.items():
                for error in errors:
                    field_name = form[field].label if field in form.fields else field
                    messages.error(request, f"{error}")
    else:
        form = CustomAuthenticationForm()
    return render(request, 'login.html', {'form': form})


def quiz_view(request):
    tags = Tag.objects.all().order_by('name')
    return render(request, 'quiz.html', {'tags': tags})


def explore_view(request):
    recommended_forums = []

    if request.user.is_authenticated:
        try:
            user_interests = request.user.userprofile.interests.all()

            if user_interests:
                forums = Forum.objects.filter(tags__in=user_interests).distinct()

                for forum in forums:
                    common_tags = forum.tags.filter(id__in=user_interests.values_list('id', flat=True))
                    recommended_forums.append({
                        "id": forum.id,
                        "title": forum.title,
                        "description": forum.description,
                        "common_tags": list(common_tags.values_list('name', flat=True)),
                        "match_score": common_tags.count()
                    })

                recommended_forums = sorted(recommended_forums, key=lambda x: x["match_score"], reverse=True)
                recommended_forums = recommended_forums[:5]
        except AttributeError:
            pass

    if not recommended_forums:
        recommended_forums = request.session.get('recommended_forums', [])

    return render(request, 'explore.html', {'recommended_forums': recommended_forums})


@login_required
def save_interests(request):
    if request.method == 'POST':
        interest_ids = request.POST.getlist('interests')

        user_profile = request.user.userprofile

        user_profile.interests.clear()
        for interest_id in interest_ids:
            try:
                tag = Tag.objects.get(id=interest_id)
                user_profile.interests.add(tag)
            except Tag.DoesNotExist:
                pass

        return redirect('users:explore')

    return redirect('users:quiz')


@csrf_exempt
def forum_recommendations(request):
    if request.method == "POST":
        try:
            logger.info("Request body: %s", request.body)
            data = json.loads(request.body)
            selected_interests = data.get("interests", [])

            forums = Forum.objects.all()
            logger.info("Forums retrieved: %s", forums)

            if not selected_interests:
                return JsonResponse({"success": False, "error": "No interests selected"}, status=400)

            recommended_forums = []
            selected_interests_cleaned = [interest.lower().strip() for interest in selected_interests]

            for forum in forums:
                forum_keywords = set(forum.title.lower().split())
                common_keywords = set(selected_interests_cleaned) & forum_keywords
                common_count = len(common_keywords)

                if common_count > 0:
                    recommended_forums.append({
                        "id": forum.id,
                        "title": forum.title,
                        "description": forum.description,
                        "common_keywords": list(common_keywords),
                        "match_score": common_count
                    })

            recommended_forums = sorted(recommended_forums, key=lambda x: x["match_score"], reverse=True)

            recommended_forums = recommended_forums[:5]

            request.session['recommended_forums'] = recommended_forums

            logger.info("Recommendations: %s", recommended_forums)

            return JsonResponse({"success": True, "recommendations": recommended_forums})

        except Exception as e:
            logger.error("Error: %s", str(e))
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)


def edit_profile_view(request):
    profile = request.user.userprofile

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)

        if 'profile_pic-clear' in request.POST and request.POST['profile_pic-clear'] == 'on':
            if profile.profile_pic:
                try:
                    profile_pic_path = profile.profile_pic.path

                    profile.profile_pic = None
                    profile.save()

                    if os.path.isfile(profile_pic_path):
                        os.remove(profile_pic_path)
                        logger.info(f"Deleted profile picture for user {request.user.username}")
                except Exception as e:
                    logger.error(f"Error deleting profile picture for user {request.user.username}: {str(e)}")

        elif 'profile_pic' in request.FILES and profile.profile_pic:
            try:
                old_pic_path = profile.profile_pic.path

                if os.path.isfile(old_pic_path):
                    os.remove(old_pic_path)
                    logger.info(f"Deleted old profile picture for user {request.user.username}")
            except Exception as e:
                logger.error(f"Error deleting old profile picture for user {request.user.username}: {str(e)}")

        if form.is_valid():
            form.save()
            return redirect('users:profile')
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'edit_profile.html', {'form': form})

@login_required
def admin_panel_view(request):
    # Перевірка прав доступу
    if not (hasattr(request.user, 'is_forum_moderator') and request.user.is_forum_moderator()):
        return redirect('home')
    
    return render(request, 'admin_panel.html')