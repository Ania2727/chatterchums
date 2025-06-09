import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Max
from forums.forms import *
from forums.models import *
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
from django.http import JsonResponse

def forum_list(request):
    forums = Forum.objects.annotate(
        topic_count=Count('topics'),
        last_activity=Max('topics__created_at')
    ).order_by('-last_activity')

    return render(request, 'forum_list.html', {'forums': forums})


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
    })


def create_topic(request, forum_id):
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