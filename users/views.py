import json
import logging
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout, login, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.http import JsonResponse
from forums.models import Forum, Topic, Comment, Tag
from django.contrib.auth.models import User, Group
from django.db.models import Q, Count
from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm, UserForm
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models.functions import TruncMonth
import calendar


logger = logging.getLogger(__name__)


@login_required
def profile_view(request):
    created_forums = Forum.objects.filter(creator=request.user)
    joined_forums = Forum.objects.filter(members=request.user).exclude(creator=request.user)
    recent_topics = Topic.objects.filter(author=request.user).order_by('-created_at')[:3]
    recent_comments = Comment.objects.filter(author=request.user).order_by('-created_at')[:5]

    context = {
        'user': request.user,  # додано для сумісності з шаблоном
        'created_forums': created_forums,
        'joined_forums': joined_forums,
        'recent_topics': recent_topics,
        'recent_comments': recent_comments,
        'is_own_profile': True,  # додано - завжди True для власного профілю
    }
    return render(request, 'profile.html', context)

@login_required
def view_user_profile(request, user_id):
    # Отримуємо користувача або 404
    profile_user = get_object_or_404(User, id=user_id)
    
    # Якщо це власний профіль, перенаправляємо на звичайну сторінку профілю
    if profile_user == request.user:
        return redirect('users:profile')
    
    # Отримуємо дані для чужого профілю
    created_forums = Forum.objects.filter(creator=profile_user)
    joined_forums = Forum.objects.filter(members=profile_user).exclude(creator=profile_user)
    recent_topics = Topic.objects.filter(author=profile_user).order_by('-created_at')[:3]
    recent_comments = Comment.objects.filter(author=profile_user).order_by('-created_at')[:5]
    
    context = {
        'user': profile_user,  # користувач чий профіль переглядаємо
        'created_forums': created_forums,
        'joined_forums': joined_forums,
        'recent_topics': recent_topics,
        'recent_comments': recent_comments,
        'is_own_profile': False,  # завжди False для чужого профілю
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

@login_required
def edit_profile_view(request):
    user = request.user
    profile = user.userprofile

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)

        if 'profile_pic-clear' in request.POST and request.POST['profile_pic-clear'] == 'on':
            if profile.profile_pic:
                try:
                    profile_pic_path = profile.profile_pic.path
                    profile.profile_pic = None
                    profile.save()
                    if os.path.isfile(profile_pic_path):
                        os.remove(profile_pic_path)
                        logger.info(f"Deleted profile picture for user {user.username}")
                except Exception as e:
                    logger.error(f"Error deleting profile picture for user {user.username}: {str(e)}")

        elif 'profile_pic' in request.FILES and profile.profile_pic:
            try:
                old_pic_path = profile.profile_pic.path
                if os.path.isfile(old_pic_path):
                    os.remove(old_pic_path)
                    logger.info(f"Deleted old profile picture for user {user.username}")
            except Exception as e:
                logger.error(f"Error deleting old profile picture for user {user.username}: {str(e)}")

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('users:profile')
    else:
        user_form = UserForm(instance=user)
        profile_form = UserProfileForm(instance=profile)

    return render(request, 'edit_profile.html', {
        'user_form': user_form,
        'form': profile_form
    })

@login_required
def admin_panel_view(request):
    # Перевірка прав доступу
    if not (hasattr(request.user, 'is_forum_moderator') and request.user.is_forum_moderator()):
        return redirect('home')
    
    return render(request, 'admin_panel.html')

@login_required
def add_tag(request):
    if not (hasattr(request.user, 'is_forum_admin') and request.user.is_forum_admin()):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method == 'POST':
        tag_name = request.POST.get('tag_name')
        if tag_name:
            tag, created = Tag.objects.get_or_create(name=tag_name.strip())
            if created:
                return JsonResponse({'success': True, 'tag': {'id': tag.id, 'name': tag.name}})
            else:
                return JsonResponse({'error': 'Tag already exists'}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def edit_tag(request, tag_id):
    if not (hasattr(request.user, 'is_forum_admin') and request.user.is_forum_admin()):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    tag = get_object_or_404(Tag, id=tag_id)
    if request.method == 'POST':
        new_name = request.POST.get('new_name')
        if new_name:
            tag.name = new_name.strip()
            tag.save()
            return JsonResponse({'success': True, 'tag': {'id': tag.id, 'name': tag.name}})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def delete_tag(request, tag_id):
    if not (hasattr(request.user, 'is_forum_admin') and request.user.is_forum_admin()):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    tag = get_object_or_404(Tag, id=tag_id)
    if request.method == 'POST':
        tag.delete()
        return JsonResponse({'success': True})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def list_tags(request):
    if not (hasattr(request.user, 'is_forum_admin') and request.user.is_forum_admin()):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    tags = Tag.objects.all().order_by('name')
    tags_data = [{'id': tag.id, 'name': tag.name} for tag in tags]
    
    return JsonResponse({'tags': tags_data})

@login_required
def list_users(request):
    if not (hasattr(request.user, 'is_forum_admin') and request.user.is_forum_admin()):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Отримуємо групи
    admin_group = Group.objects.get(name='administrator')
    moderator_group = Group.objects.get(name='moderator')
    
    # Фільтри
    role_filter = request.GET.get('role', 'all')  # all, admin, moderator, regular
    search_query = request.GET.get('search', '')
    
    # Базовий запит
    users = User.objects.all()
    
    # Пошук за username або email
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) | 
            Q(email__icontains=search_query)
        )
    
    # Фільтр за ролями
    if role_filter == 'admin':
        users = users.filter(groups=admin_group)
    elif role_filter == 'moderator':
        users = users.filter(groups=moderator_group).exclude(groups=admin_group)
    elif role_filter == 'regular':
        users = users.exclude(groups__in=[admin_group, moderator_group])
    
    users_data = []
    for user in users[:50]:  # Обмежуємо 50 користувачами
        is_admin = user.groups.filter(name='administrator').exists()
        is_moderator = user.groups.filter(name='moderator').exists()
        
        role = 'Administrator' if is_admin else ('Moderator' if is_moderator else 'User')
        
        users_data.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'date_joined': user.date_joined.strftime('%Y-%m-%d'),
            'is_admin': is_admin,
            'is_moderator': is_moderator,
            'role': role
        })
    
    return JsonResponse({'users': users_data})

@login_required
def promote_to_moderator(request, user_id):
    if not (hasattr(request.user, 'is_forum_admin') and request.user.is_forum_admin()):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        moderator_group = Group.objects.get(name='moderator')
        
        if not user.groups.filter(name='moderator').exists():
            user.groups.add(moderator_group)
            return JsonResponse({'success': True, 'message': f'{user.username} promoted to moderator'})
        else:
            return JsonResponse({'error': 'User is already a moderator'}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def promote_to_admin(request, user_id):
    if not (hasattr(request.user, 'is_forum_admin') and request.user.is_forum_admin()):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        admin_group = Group.objects.get(name='administrator')
        moderator_group = Group.objects.get(name='moderator')
        
        if not user.groups.filter(name='administrator').exists():
            user.groups.add(admin_group)
            # Адмін автоматично є модератором
            if not user.groups.filter(name='moderator').exists():
                user.groups.add(moderator_group)
            return JsonResponse({'success': True, 'message': f'{user.username} promoted to administrator'})
        else:
            return JsonResponse({'error': 'User is already an administrator'}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def remove_moderator(request, user_id):
    if not (hasattr(request.user, 'is_forum_admin') and request.user.is_forum_admin()):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        
        # Не можна забрати права у себе
        if user.id == request.user.id:
            return JsonResponse({'error': 'Cannot remove your own moderator rights'}, status=400)
        
        moderator_group = Group.objects.get(name='moderator')
        
        if user.groups.filter(name='moderator').exists():
            user.groups.remove(moderator_group)
            return JsonResponse({'success': True, 'message': f'Moderator rights removed from {user.username}'})
        else:
            return JsonResponse({'error': 'User is not a moderator'}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def remove_admin(request, user_id):
    if not (hasattr(request.user, 'is_forum_admin') and request.user.is_forum_admin()):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        
        # Не можна забрати права у себе
        if user.id == request.user.id:
            return JsonResponse({'error': 'Cannot remove your own admin rights'}, status=400)
        
        admin_group = Group.objects.get(name='administrator')
        
        if user.groups.filter(name='administrator').exists():
            user.groups.remove(admin_group)
            return JsonResponse({'success': True, 'message': f'Admin rights removed from {user.username}'})
        else:
            return JsonResponse({'error': 'User is not an administrator'}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def management_stats(request):
    if not (hasattr(request.user, 'is_forum_admin') and request.user.is_forum_admin()):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    admin_group = Group.objects.get(name='administrator')
    moderator_group = Group.objects.get(name='moderator')
    
    admin_count = User.objects.filter(groups=admin_group).count()
    moderator_count = User.objects.filter(groups=moderator_group).exclude(groups=admin_group).count()
    total_users = User.objects.count()
    
    return JsonResponse({
        'admin_count': admin_count,
        'moderator_count': moderator_count,
        'total_users': total_users
    })

@login_required
def search_users(request):
    if not (hasattr(request.user, 'is_forum_admin') and request.user.is_forum_admin()):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'users': []})
    
    users = User.objects.filter(
        Q(username__icontains=query) | Q(email__icontains=query)
    ).exclude(is_superuser=True)[:10]  # Виключаємо суперюзерів, обмежуємо 10 результатами
    
    admin_group = Group.objects.get(name='administrator')
    moderator_group = Group.objects.get(name='moderator')
    
    users_data = []
    for user in users:
        is_admin = user.groups.filter(name='administrator').exists()
        is_moderator = user.groups.filter(name='moderator').exists()
        role = 'Administrator' if is_admin else ('Moderator' if is_moderator else 'User')
        
        users_data.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_admin': is_admin,
            'is_moderator': is_moderator,
            'role': role
        })
    
    return JsonResponse({'users': users_data})

@login_required
def view_user_profile(request, user_id):
    profile_user = get_object_or_404(User, id=user_id)
    
    created_forums = Forum.objects.filter(creator=profile_user)
    
    joined_forums = Forum.objects.filter(members=profile_user).exclude(creator=profile_user)
    
    recent_topics = Topic.objects.filter(author=profile_user).order_by('-created_at')[:3]
    recent_comments = Comment.objects.filter(author=profile_user).order_by('-created_at')[:5]
    
    is_own_profile = request.user == profile_user
    
    context = {
        'user': profile_user,
        'created_forums': created_forums,
        'joined_forums': joined_forums,
        'recent_topics': recent_topics,
        'recent_comments': recent_comments,
        'is_own_profile': is_own_profile,
    }
    
    return render(request, 'profile.html', context)

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('users:change_password_done')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, 'change_password.html', {'form': form})

@login_required
def change_password_done(request):
    return render(request, 'change_password_done.html')

@login_required
def forum_statistics(request):
    today = timezone.now()
    thirty_days_ago = today - timedelta(days=30)

    total_users = User.objects.count()
    total_forums = Forum.objects.count()
    total_topics = Topic.objects.count()
    total_comments = Comment.objects.count()

    active_users_30_days = User.objects.filter(
        last_login__gte=thirty_days_ago
    ).count()

    first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_users_this_month = User.objects.filter(
        date_joined__gte=first_day_of_month
    ).count()

    today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
    topics_today = Topic.objects.filter(created_at__gte=today_start).count()
    comments_today = Comment.objects.filter(created_at__gte=today_start).count()
    posts_today = topics_today + comments_today

    twelve_months_ago = today - timedelta(days=365)
    registration_stats = User.objects.filter(
        date_joined__gte=twelve_months_ago
    ).annotate(
        month=TruncMonth('date_joined')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')

    registration_months = []
    registration_data = []
    
    for i in range(12):
        month_date = (today.replace(day=1) - timedelta(days=30*i)).replace(day=1)
        registration_months.insert(0, month_date.strftime("%b %Y"))
        
        month_count = 0
        for stat in registration_stats:
            if stat['month'].year == month_date.year and stat['month'].month == month_date.month:
                month_count = stat['count']
                break
        registration_data.insert(0, month_count)

    raw_top_forums = Forum.objects.annotate(
        topic_count=Count('topics'),
        total_comments=Count('topics__comments')
    ).order_by('-topic_count', '-total_comments')[:5]

    max_activity = max(
        [(f.topic_count + f.total_comments) for f in raw_top_forums], 
        default=1
    )

    top_forums = []
    for forum in raw_top_forums:
        total_activity = forum.topic_count + forum.total_comments
        top_forums.append({
            "name": forum.title,
            "topic_count": forum.topic_count,
            "total_comments": forum.total_comments,
            "activity_percentage": round((total_activity / max_activity * 100), 1)
        })

    most_active_forum = top_forums[0] if top_forums else {
        "name": "N/A",
        "topic_count": 0
    }

    return JsonResponse({
        "total_users": total_users,
        "total_forums": total_forums,
        "total_topics": total_topics,
        "total_comments": total_comments,
        "active_users_30_days": active_users_30_days,
        "new_users_this_month": new_users_this_month,
        "posts_today": posts_today,
        "most_active_forum": {
            "name": most_active_forum["name"],
            "topic_count": most_active_forum["topic_count"]
        },
        "registration_months": registration_months,
        "registration_data": registration_data,
        "top_forums": top_forums,
    })

@login_required
def admin_complaints_view(request):
    complaints = Complaint.objects.select_related(
        'author', 'user_target', 'forum_target', 'topic_target', 'comment_target'
    ).order_by('-complaint_time')
    return render(request, 'admin/complaints.html', {
        'complaints': complaints
    })