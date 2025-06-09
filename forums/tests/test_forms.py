import pytest
from django.test import RequestFactory
from forums.forms import CreateInForum, TopicForm, CommentForm
from forums.tests.factories import UserFactory, TagFactory, ForumFactory, TopicFactory


@pytest.mark.django_db
class TestCreateInForumForm:
    def test_form_valid_data(self):
        user = UserFactory()
        tag1 = TagFactory()
        tag2 = TagFactory()
        
        form_data = {
            'title': 'Test Forum',
            'description': 'Test Description',
            'link': 'https://example.com',
            'tags': [tag1.id, tag2.id]
        }
        
        form = CreateInForum(data=form_data, user=user)
        assert form.is_valid()
    
    def test_form_save_with_user(self):
        user = UserFactory()
        tag = TagFactory()
        
        form_data = {
            'title': 'Test Forum',
            'description': 'Test Description',
            'tags': [tag.id]
        }
        
        form = CreateInForum(data=form_data, user=user)
        assert form.is_valid()
        
        forum = form.save()
        assert forum.creator == user
        assert forum.name == user.username
        assert user in forum.members.all()
        assert tag in forum.tags.all()
    
    def test_form_link_not_required(self):
        user = UserFactory()
        
        form_data = {
            'title': 'Test Forum',
            'description': 'Test Description'
        }
        
        form = CreateInForum(data=form_data, user=user)
        assert form.is_valid()
    
    def test_form_invalid_link(self):
        user = UserFactory()
        
        form_data = {
            'title': 'Test Forum',
            'description': 'Test Description',
            'link': 'not-a-valid-url'
        }
        
        form = CreateInForum(data=form_data, user=user)
        assert not form.is_valid()
        assert 'link' in form.errors


@pytest.mark.django_db
class TestTopicForm:
    def test_form_valid_data(self):
        user = UserFactory()
        forum = ForumFactory()
        
        form_data = {
            'title': 'Test Topic',
            'content': 'Test Content'
        }
        
        form = TopicForm(data=form_data, user=user, forum=forum)
        assert form.is_valid()
    
    def test_form_save_with_user_and_forum(self):
        user = UserFactory()
        forum = ForumFactory()
        
        form_data = {
            'title': 'Test Topic',
            'content': 'Test Content'
        }
        
        form = TopicForm(data=form_data, user=user, forum=forum)
        assert form.is_valid()
        
        topic = form.save()
        assert topic.author == user
        assert topic.forum == forum
    
    def test_form_required_fields(self):
        user = UserFactory()
        forum = ForumFactory()
        
        # Test missing title
        form = TopicForm(data={'content': 'Test'}, user=user, forum=forum)
        assert not form.is_valid()
        assert 'title' in form.errors
        
        # Test missing content
        form = TopicForm(data={'title': 'Test'}, user=user, forum=forum)
        assert not form.is_valid()
        assert 'content' in form.errors
    
    def test_form_edit_existing_topic(self):
        topic = TopicFactory()
        user = topic.author
        forum = topic.forum
        
        form_data = {
            'title': 'Updated Title',
            'content': 'Updated Content'
        }
        
        form = TopicForm(data=form_data, instance=topic, user=user, forum=forum)
        assert form.is_valid()
        
        updated_topic = form.save()
        assert updated_topic.title == 'Updated Title'
        assert updated_topic.content == 'Updated Content'


@pytest.mark.django_db
class TestCommentForm:
    def test_form_valid_data(self):
        user = UserFactory()
        topic = TopicFactory()
        
        form_data = {
            'content': 'Test Comment'
        }
        
        form = CommentForm(data=form_data, user=user, topic=topic)
        assert form.is_valid()
    
    def test_form_save_with_user_and_topic(self):
        user = UserFactory()
        topic = TopicFactory()
        
        form_data = {
            'content': 'Test Comment'
        }
        
        form = CommentForm(data=form_data, user=user, topic=topic)
        assert form.is_valid()
        
        comment = form.save()
        assert comment.author == user
        assert comment.topic == topic
    
    def test_form_required_content(self):
        user = UserFactory()
        topic = TopicFactory()
        
        form = CommentForm(data={}, user=user, topic=topic)
        assert not form.is_valid()
        assert 'content' in form.errors
    
    def test_form_edit_existing_comment(self):
        from forums.tests.factories import CommentFactory
        comment = CommentFactory()
        user = comment.author
        topic = comment.topic
        
        form_data = {
            'content': 'Updated Comment'
        }
        
        form = CommentForm(data=form_data, instance=comment, user=user, topic=topic)
        assert form.is_valid()
        
        updated_comment = form.save()
        assert updated_comment.content == 'Updated Comment'