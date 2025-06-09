import pytest
from django.test import Client, RequestFactory
from django.urls import reverse
from django.contrib.messages import get_messages
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from unittest.mock import patch, MagicMock
from forums.views import *
from forums.models import Tag
from forums.tests.factories import UserFactory, TagFactory, ForumFactory, TopicFactory, CommentFactory


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def authenticated_user():
    user = UserFactory()
    return user


@pytest.fixture
def authenticated_client(client, authenticated_user):
    client.force_login(authenticated_user)
    return client


@pytest.fixture(autouse=True)
def auto_mock_render(monkeypatch):
    def _mock_render(request, template_name, context=None, *args, **kwargs):
        return HttpResponse(f"Rendered: {template_name}")
    monkeypatch.setattr('django.shortcuts.render', _mock_render)


@pytest.mark.django_db
class TestForumListView:
    def test_forum_list_view(self, client):
        forum1 = ForumFactory()
        forum2 = ForumFactory()
        forum3 = ForumFactory()
        
        TopicFactory(forum=forum2)
        
        response = client.get(reverse('forums:forum_list'))
        assert response.status_code == 200
    
    def test_forum_list_ordering_by_last_activity(self, client):
        forum1 = ForumFactory()
        forum2 = ForumFactory()
        
        TopicFactory(forum=forum2)
        
        response = client.get(reverse('forums:forum_list'))
        assert response.status_code == 200


@pytest.mark.django_db
class TestUserForumsView:
    def test_user_forums_requires_login(self, client):
        response = client.get(reverse('forums:user_forums'))
        assert response.status_code == 302
        assert '/login/' in response.url
    


@pytest.mark.django_db
class TestAddForumView:
    def test_add_forum_requires_login(self, client):
        response = client.get(reverse('forums:add_forum'))
        assert response.status_code == 302
        assert '/login/' in response.url
    
    def test_add_forum_creates_default_tags(self, authenticated_client):
        Tag.objects.all().delete()
        
        response = authenticated_client.get(reverse('forums:add_forum'))
        assert response.status_code == 200
        
        assert Tag.objects.count() > 0
        assert Tag.objects.filter(name='Technology').exists()
    
    def test_add_forum_post_valid(self, authenticated_client, authenticated_user):
        tag = TagFactory()
        
        data = {
            'title': 'New Forum',
            'description': 'Forum Description',
            'tags': [tag.id]
        }
        
        response = authenticated_client.post(reverse('forums:add_forum'), data)
        
        assert response.status_code == 302
        
        forum = Forum.objects.get(title='New Forum')
        assert forum.creator == authenticated_user
        assert authenticated_user in forum.members.all()
        assert tag in forum.tags.all()


@pytest.mark.django_db
class TestForumDetailView:
    def test_forum_detail_view(self, client):
        forum = ForumFactory()
        topic1 = TopicFactory(forum=forum)
        topic2 = TopicFactory(forum=forum)
        
        response = client.get(reverse('forums:forum_detail', args=[forum.id]))
        assert response.status_code == 200
    
    def test_forum_detail_membership_status(self, authenticated_client, authenticated_user):
        forum = ForumFactory()
        forum.members.add(authenticated_user)
        
        response = authenticated_client.get(reverse('forums:forum_detail', args=[forum.id]))
        assert response.status_code == 200
    
    def test_forum_detail_non_member(self, authenticated_client):
        forum = ForumFactory()
        
        response = authenticated_client.get(reverse('forums:forum_detail', args=[forum.id]))
        assert response.status_code == 200


@pytest.mark.django_db
class TestCreateTopicView:
    def test_create_topic_requires_membership(self, authenticated_client):
        forum = ForumFactory()
        
        response = authenticated_client.get(reverse('forums:create_topic', args=[forum.id]))
        assert response.status_code == 403
    
    def test_create_topic_member_can_access(self, authenticated_client, authenticated_user):
        forum = ForumFactory()
        forum.members.add(authenticated_user)
        
        response = authenticated_client.get(reverse('forums:create_topic', args=[forum.id]))
        assert response.status_code == 200
    
    def test_create_topic_post_valid(self, authenticated_client, authenticated_user):
        forum = ForumFactory()
        forum.members.add(authenticated_user)
        
        data = {
            'title': 'New Topic',
            'content': 'Topic Content'
        }
        
        response = authenticated_client.post(
            reverse('forums:create_topic', args=[forum.id]), 
            data
        )
        
        assert response.status_code == 302
        
        topic = Topic.objects.get(title='New Topic')
        assert topic.forum == forum
        assert topic.author == authenticated_user


@pytest.mark.django_db
class TestTopicDetailView:
    def test_topic_detail_increments_views(self, client):
        topic = TopicFactory(views=0)
        
        response = client.get(
            reverse('forums:topic_detail', args=[topic.forum.id, topic.id])
        )
        
        assert response.status_code == 200
        topic.refresh_from_db()
        assert topic.views == 1
    
    def test_topic_detail_shows_comments(self, client):
        topic = TopicFactory()
        comment1 = CommentFactory(topic=topic)
        comment2 = CommentFactory(topic=topic)
        
        response = client.get(
            reverse('forums:topic_detail', args=[topic.forum.id, topic.id])
        )
        
        assert response.status_code == 200


@pytest.mark.django_db
class TestEditTopicView:
    def test_edit_topic_requires_author(self, authenticated_client):
        topic = TopicFactory()
        
        response = authenticated_client.get(
            reverse('forums:edit_topic', args=[topic.forum.id, topic.id])
        )
        
        assert response.status_code == 403
    
    def test_edit_topic_author_can_edit(self, authenticated_client, authenticated_user):
        topic = TopicFactory(author=authenticated_user)
        
        response = authenticated_client.get(
            reverse('forums:edit_topic', args=[topic.forum.id, topic.id])
        )
        
        assert response.status_code == 200
    
    def test_edit_topic_post_valid(self, authenticated_client, authenticated_user):
        topic = TopicFactory(author=authenticated_user)
        
        data = {
            'title': 'Updated Title',
            'content': 'Updated Content'
        }
        
        response = authenticated_client.post(
            reverse('forums:edit_topic', args=[topic.forum.id, topic.id]),
            data
        )
        
        assert response.status_code == 302
        
        topic.refresh_from_db()
        assert topic.title == 'Updated Title'
        assert topic.content == 'Updated Content'
