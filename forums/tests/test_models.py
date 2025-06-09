import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from forums.models import Tag, Forum, Topic, Comment
from forums.tests.factories import UserFactory, TagFactory, ForumFactory, TopicFactory, CommentFactory


@pytest.mark.django_db
class TestTagModel:
    def test_tag_str_representation(self):
        tag = TagFactory(name="Technology")
        assert str(tag) == "Technology"
    
    def test_tag_ordering(self):
        tag1 = TagFactory(name="Zebra")
        tag2 = TagFactory(name="Apple")
        tag3 = TagFactory(name="Monkey")
        
        tags = Tag.objects.all()
        assert list(tags) == [tag2, tag3, tag1]
    
    def test_tag_unique_name(self):
        TagFactory(name="UniqueTag")
        with pytest.raises(Exception):
            TagFactory(name="UniqueTag")


@pytest.mark.django_db
class TestForumModel:
    def test_forum_str_representation(self):
        forum = ForumFactory(title="Test Forum")
        assert str(forum) == "Test Forum"
    
    def test_forum_get_absolute_url(self):
        forum = ForumFactory()
        expected_url = reverse('forums:forum_detail', args=[str(forum.id)])
        assert forum.get_absolute_url() == expected_url
    
    def test_forum_creator_relationship(self):
        user = UserFactory()
        forum = ForumFactory(creator=user)
        assert forum.creator == user
        assert forum in user.created_forums.all()
    
    def test_forum_members_relationship(self):
        forum = ForumFactory()
        user1 = UserFactory()
        user2 = UserFactory()
        
        forum.members.add(user1, user2)
        
        assert user1 in forum.members.all()
        assert user2 in forum.members.all()
        assert forum in user1.joined_forums.all()
    
    def test_forum_tags_relationship(self):
        forum = ForumFactory()
        tag1 = TagFactory()
        tag2 = TagFactory()
        
        forum.tags.add(tag1, tag2)
        
        assert tag1 in forum.tags.all()
        assert tag2 in forum.tags.all()
        assert forum in tag1.forums.all()


@pytest.mark.django_db
class TestTopicModel:
    def test_topic_str_representation(self):
        topic = TopicFactory(title="Test Topic")
        assert str(topic) == "Test Topic"
    
    def test_topic_get_absolute_url(self):
        forum = ForumFactory()
        topic = TopicFactory(forum=forum)
        expected_url = reverse('forums:topic_detail', args=[str(forum.id), str(topic.id)])
        assert topic.get_absolute_url() == expected_url
    
    def test_topic_ordering(self):
        topic1 = TopicFactory()
        topic2 = TopicFactory()
        topic3 = TopicFactory()
        
        topics = Topic.objects.all()
        # Should be ordered by created_at descending
        assert list(topics) == [topic3, topic2, topic1]
    
    def test_topic_forum_relationship(self):
        forum = ForumFactory()
        topic = TopicFactory(forum=forum)
        assert topic.forum == forum
        assert topic in forum.topics.all()
    
    def test_topic_author_relationship(self):
        user = UserFactory()
        topic = TopicFactory(author=user)
        assert topic.author == user
        assert topic in user.topics.all()
    
    def test_topic_default_views(self):
        topic = TopicFactory()
        assert topic.views == 0


@pytest.mark.django_db
class TestCommentModel:
    def test_comment_str_representation(self):
        user = UserFactory(username="testuser")
        topic = TopicFactory(title="Test Topic")
        comment = CommentFactory(author=user, topic=topic)
        assert str(comment) == "Comment by testuser on Test Topic"
    
    def test_comment_ordering(self):
        topic = TopicFactory()
        comment1 = CommentFactory(topic=topic)
        comment2 = CommentFactory(topic=topic)
        comment3 = CommentFactory(topic=topic)
        
        comments = Comment.objects.filter(topic=topic)
        # Should be ordered by created_at ascending
        assert list(comments) == [comment1, comment2, comment3]
    
    def test_comment_topic_relationship(self):
        topic = TopicFactory()
        comment = CommentFactory(topic=topic)
        assert comment.topic == topic
        assert comment in topic.comments.all()
    
    def test_comment_author_relationship(self):
        user = UserFactory()
        comment = CommentFactory(author=user)
        assert comment.author == user
        assert comment in user.comments.all()