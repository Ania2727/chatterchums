import json

from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Max, Q
from django.views.decorators.http import require_POST
from forums.forms import *
from forums.models import *
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
from django.template.loader import render_to_string
from django.http import JsonResponse

def forum_list(request):
    # Базовий QuerySet
    forums = Forum.objects.annotate(
        topic_count=Count('topics'),
        last_activity=Max('topics__created_at')
    )
    
    # Отримуємо параметри з URL
    search_query = request.GET.get('search', '').strip()
    tag_filter = request.GET.getlist('tag')  # Змінено на getlist для підтримки кількох тегів
    sort_option = request.GET.get('sort', 'newest')
    
    # Пошук за назвою та описом
    if search_query:
        forums = forums.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Фільтрація за тегами (підтримка кількох тегів)
    if tag_filter:
        tag_ids = request.GET.getlist('tag')  # Отримуємо список тегів
        if tag_ids:
            try:
                # Конвертуємо в числа та фільтруємо валідні ID
                valid_tag_ids = [int(tag_id) for tag_id in tag_ids if tag_id.isdigit()]
                if valid_tag_ids:
                    # Фільтруємо форуми, які мають хоча б один з вибраних тегів
                    forums = forums.filter(tags__id__in=valid_tag_ids).distinct()
            except (ValueError, TypeError):
                pass
    
    # Сортування
    if sort_option == 'newest':
        forums = forums.order_by('-date_posted')
    elif sort_option == 'oldest':
        forums = forums.order_by('date_posted')
    elif sort_option == 'most_topics':
        forums = forums.order_by('-topic_count')
    elif sort_option == 'most_members':
        forums = forums.annotate(member_count=Count('members')).order_by('-member_count')
    elif sort_option == 'alphabetical':
        forums = forums.order_by('title')
    elif sort_option == 'last_activity':
        forums = forums.order_by('-last_activity')
    else:
        forums = forums.order_by('-last_activity')  # За замовчуванням
    
    # Отримуємо всі доступні теги для фільтра
    all_tags = Tag.objects.all().order_by('name')
    
    # Отримуємо вибрані теги для передачі в шаблон
    selected_tag_ids = [int(tag_id) for tag_id in tag_filter if tag_id.isdigit()]
    
    return render(request, 'forum_list.html', {
        'forums': forums,
        'all_tags': all_tags,
        'selected_tag_ids': selected_tag_ids,
    })


@login_required
def user_forums(request):
    user_created_forums = Forum.objects.filter(creator=request.user).order_by('-date_posted')
    user_member_forums = Forum.objects.filter(members=request.user).exclude(creator=request.user).order_by(
        '-date_posted')
    other_forums = Forum.objects.exclude(creator=request.user).exclude(members=request.user).order_by('-date_posted')

    return render(request, 'user_forums.html', {
        'created_forums': user_created_forums,
        'member_forums': user_member_forums,
        'forums': other_forums
    })


@login_required
def add_forum(request):
    # Create tags if no tags exist
    if Tag.objects.count() == 0:
        tags = [
            # General Categories
            'Technology', 'Gaming', 'Entertainment', 'Sports', 'Science',
            'Art', 'Music', 'Movies', 'Books', 'Food', 'Travel', 'Fashion',
            'Health', 'Fitness', 'Politics', 'Business', 'Finance', 'Education',
            'TV Shows', 'Anime', 'Comics', 'Podcasts', 'Celebrities',
            'Rock', 'Pop', 'Hip-Hop', 'Jazz', 'Classical', 'Electronic',
            'Humor', 'News', 'History', 'Philosophy', 'Psychology'
        ]
        for tag_name in tags:
            Tag.objects.get_or_create(name=tag_name)

    if request.method == 'POST':
        form = CreateInForum(request.POST, user=request.user)
        if form.is_valid():
            forum_obj = form.save()
            return redirect('forums:forum_detail', forum_id=forum_obj.id)
    else:
        form = CreateInForum(user=request.user)

    return render(request, 'add_forum.html', {'form': form})


def forum_detail(request, forum_id):
    forum = get_object_or_404(Forum, id=forum_id)
    topics = forum.topics.annotate(comment_count=Count('comments')).order_by('-created_at')

    is_member = request.user.is_authenticated and forum.members.filter(id=request.user.id).exists()

    return render(request, 'forum_detail.html', {
        'forum': forum,
        'topics': topics,
        'is_member': is_member,
        'complaint_reasons': Complaint.COMPLAINT_REASONS,
    })


def create_topic(request, forum_id):
    """
       Handles the creation of a new topic within a specific forum.

       Args:
           request (HttpRequest): The HTTP request object containing user data and form submission.
           forum_id (int): The ID of the forum where the topic is being created.
       Returns:
           HttpResponse: Redirects to the topic detail page if the topic is successfully created.
           HttpResponseForbidden: Returns a forbidden response if the user is not a member of the forum.
           HttpResponse: Renders the topic creation form if the request method is GET.
       """
    forum = get_object_or_404(Forum, id=forum_id)

    if not forum.members.filter(id=request.user.id).exists():
        return HttpResponseForbidden("You must be a member of this forum to create topics")

    if request.method == 'POST':
        form = TopicForm(request.POST, user=request.user, forum=forum)
        if form.is_valid():
            topic = form.save()
            messages.success(request, 'Topic created successfully!')
            return redirect('forums:topic_detail', forum_id=forum.id, topic_id=topic.id)
    else:
        form = TopicForm(user=request.user, forum=forum)

    return render(request, 'create_topic.html', {
        'form': form,
        'forum': forum
    })


def topic_detail(request, forum_id, topic_id):
    forum = get_object_or_404(Forum, id=forum_id)
    topic = get_object_or_404(Topic, id=topic_id, forum=forum)
    comments = topic.comments.all()

    # Increment view count
    topic.views += 1
    topic.save()

    comment_form = CommentForm(user=request.user, topic=topic)

    return render(request, 'topic_detail.html', {
        'forum': forum,
        'topic': topic,
        'comments': comments,
        'comment_form': comment_form
    })


@login_required
def edit_topic(request, forum_id, topic_id):
    forum = get_object_or_404(Forum, id=forum_id)
    topic = get_object_or_404(Topic, id=topic_id, forum=forum)

    # Check if user is the author
    if topic.author != request.user:
        return HttpResponseForbidden("You don't have permission to edit this topic")

    if request.method == 'POST':
        form = TopicForm(request.POST, instance=topic, user=request.user, forum=forum)
        if form.is_valid():
            form.save()
            messages.success(request, 'Topic updated successfully!')
            return redirect('forums:topic_detail', forum_id=forum.id, topic_id=topic.id)
    else:
        form = TopicForm(instance=topic, user=request.user, forum=forum)

    return render(request, 'edit_topic.html', {
        'form': form,
        'forum': forum,
        'topic': topic
    })


@login_required
def add_comment(request, forum_id, topic_id):
    forum = get_object_or_404(Forum, id=forum_id)
    topic = get_object_or_404(Topic, id=topic_id, forum=forum)

    if request.method == 'POST':
        form = CommentForm(request.POST, user=request.user, topic=topic)
        if form.is_valid():
            form.save()
            messages.success(request, 'Comment added!')
            return redirect('forums:topic_detail', forum_id=forum.id, topic_id=topic.id)
    else:
        return redirect('forums:topic_detail', forum_id=forum.id, topic_id=topic.id)


@login_required
def edit_comment(request, forum_id, topic_id, comment_id):
    forum = get_object_or_404(Forum, id=forum_id)
    topic = get_object_or_404(Topic, id=topic_id, forum=forum)
    comment = get_object_or_404(Comment, id=comment_id, topic=topic)

    # Check if user is the author
    if comment.author != request.user:
        return HttpResponseForbidden("You don't have permission to edit this comment")

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment, user=request.user, topic=topic)
        if form.is_valid():
            form.save()
            messages.success(request, 'Comment updated!')
            return redirect('forums:topic_detail', forum_id=forum.id, topic_id=topic.id)
    else:
        form = CommentForm(instance=comment, user=request.user, topic=topic)

    return render(request, 'edit_comment.html', {
        'form': form,
        'forum': forum,
        'topic': topic,
        'comment': comment
    })


@login_required
def join_forum(request, forum_id):
    forum_obj = get_object_or_404(Forum, id=forum_id)

    # Add user to forum members
    forum_obj.members.add(request.user)
    messages.success(request, f'You have joined {forum_obj.title}')

    return redirect('forums:forum_detail', forum_id=forum_obj.id)


@login_required
def leave_forum(request, forum_id):
    forum_obj = get_object_or_404(Forum, id=forum_id)

    # Remove user from forum members
    forum_obj.members.remove(request.user)
    messages.info(request, f'You have left {forum_obj.title}')

    return redirect('forums:forum_list')


def home(request):
    # Get 3 forums with the most members
    forums = Forum.objects.annotate(member_count=Count('members')).order_by('-member_count')[:3]
    return render(request, 'home.html', {'forums': forums})

@login_required
def delete_comment(request, forum_id, topic_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, topic_id=topic_id)

    if request.user == comment.author or (hasattr(request.user, 'is_forum_moderator') and request.user.is_forum_moderator()):
        if request.method == 'POST':
            comment.delete()
            messages.success(request, 'Comment deleted successfully.')
        return redirect('forums:topic_detail', forum_id=forum_id, topic_id=topic_id)
    else:
        messages.error(request, 'You do not have permission to delete this comment.')
        return redirect('forums:topic_detail', forum_id=forum_id, topic_id=topic_id)

@login_required
def add_comment_ajax(request, forum_id, topic_id):
    if request.method == 'POST':
        forum = get_object_or_404(Forum, id=forum_id)
        topic = get_object_or_404(Topic, id=topic_id, forum=forum)

        form = CommentForm(request.POST, user=request.user, topic=topic)
        if form.is_valid():
            comment = form.save()

            # Render comment HTML
            comment_html = render_to_string('partials/comment_item.html', {
                'comment': comment,
                'user': request.user,
                'forum': forum,
                'topic': topic
            })

            return JsonResponse({
                'success': True,
                'comment_html': comment_html,
                'comment_count': topic.comments.count()
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })

    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def delete_comment_ajax(request, forum_id, topic_id, comment_id):
    if request.method == 'POST':
        comment = get_object_or_404(Comment, id=comment_id, topic_id=topic_id)

        if request.user == comment.author or (hasattr(request.user, 'is_forum_moderator') and request.user.is_forum_moderator()):
            comment.delete()
            topic = get_object_or_404(Topic, id=topic_id)

            return JsonResponse({
                'success': True,
                'comment_count': topic.comments.count()
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Permission denied'
            })

    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def edit_comment_ajax(request, forum_id, topic_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, topic_id=topic_id)

    if comment.author != request.user:
        return JsonResponse({'success': False, 'error': 'Permission denied'})

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment, user=request.user, topic=comment.topic)
        if form.is_valid():
            form.save()
            return JsonResponse({
                'success': True,
                'content': comment.content
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })

    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def edit_forum(request, forum_id):
    forum = get_object_or_404(Forum, id=forum_id)
    if not request.user.is_forum_admin():
        return HttpResponseForbidden("You don't have permission to edit this forum.")

    if request.method == 'POST':
        form = CreateInForum(request.POST, instance=forum, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Forum updated successfully!')
            return redirect('forums:forum_detail', forum_id=forum.id)
    else:
        form = CreateInForum(instance=forum, user=request.user)

    return render(request, 'edit_forum.html', {'form': form, 'forum': forum})


@login_required
def delete_forum(request, forum_id):
    forum = get_object_or_404(Forum, id=forum_id)
    if not request.user.is_forum_admin():
        return HttpResponseForbidden("You don't have permission to delete this forum.")

    if request.method == 'POST':
        forum.delete()
        messages.success(request, 'Forum deleted successfully!')
        return redirect('forums:forum_list')

    return render(request, 'confirm_delete_forum.html', {'forum': forum})

#@require_POST
@login_required
def submit_complaint_ajax(request):
    user = request.user
    complaint_text = request.POST.get('complaint_text', '').strip()
    complaint_type = request.POST.get('complaint_type')
    target_type = request.POST.get('target_type')
    target_id = request.POST.get('target_id')

    if not complaint_text or not complaint_type or not target_type or not target_id:
        return JsonResponse({'success': False, 'error': 'Missing required fields.'})

    kwargs = {
        'author': user,
        'complaint_text': complaint_text,
        'complaint_type': complaint_type,
        'status': 'pending',
    }

    try:
        if target_type == 'topic':
            from .models import Topic
            kwargs['topic_target'] = Topic.objects.get(pk=target_id)
        elif target_type == 'comment':
            from .models import Comment
            kwargs['comment_target'] = Comment.objects.get(pk=target_id)
        elif target_type == 'forum':
            kwargs['forum_target'] = Forum.objects.get(pk=target_id)
        elif target_type == 'user':
            from django.contrib.auth.models import User
            kwargs['user_target'] = User.objects.get(pk=target_id)
        else:
            return JsonResponse({'success': False, 'error': 'Invalid target type.'})

        complaint = Complaint(**kwargs)
        complaint.full_clean()  # <- валідатор (перевіряє, що тільки одна ціль задана)
        complaint.save()

        return JsonResponse({'success': True})

    except ObjectDoesNotExist:
        return JsonResponse({'success': False, 'error': 'Target does not exist.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def report_forum(request, forum_id):
    if request.method == 'POST':
        forum = get_object_or_404(Forum, id=forum_id)
        text = request.POST.get('complaint_text', '').strip()
        reason = request.POST.get('complaint_type')

        if not text or reason not in dict(Complaint.COMPLAINT_REASONS):
            messages.error(request, "Please provide valid reason and description.")
            return redirect('forums:forum_detail', forum_id=forum.id)

        Complaint.objects.create(
            author=request.user,
            complaint_text=text,
            complaint_type=reason,
            forum_target=forum
        )
        messages.success(request, "Thanks! Your complaint has been submitted.")
        return redirect('forums:forum_detail', forum_id=forum.id)

    return redirect('forums:forum_list')

