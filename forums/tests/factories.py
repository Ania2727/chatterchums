import factory
from factory.django import DjangoModelFactory
from django.contrib.auth.models import User
from forums.models import Tag, Forum, Topic, Comment


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')


class TagFactory(DjangoModelFactory):
    class Meta:
        model = Tag
    
    name = factory.Faker('word')


class ForumFactory(DjangoModelFactory):
    class Meta:
        model = Forum
    
    creator = factory.SubFactory(UserFactory)
    name = factory.LazyAttribute(lambda obj: obj.creator.username)
    title = factory.Faker('sentence', nb_words=4)
    description = factory.Faker('text', max_nb_chars=200)
    link = factory.Faker('url')
    
    @factory.post_generation
    def members(self, create, extracted, **kwargs):
        if not create:
            return
        
        if extracted:
            for member in extracted:
                self.members.add(member)
        else:
            # Add creator as member by default
            self.members.add(self.creator)
    
    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            return
        
        if extracted:
            for tag in extracted:
                self.tags.add(tag)


class TopicFactory(DjangoModelFactory):
    class Meta:
        model = Topic
    
    forum = factory.SubFactory(ForumFactory)
    author = factory.SubFactory(UserFactory)
    title = factory.Faker('sentence', nb_words=6)
    content = factory.Faker('text')
    views = 0  # Default to 0 instead of random


class CommentFactory(DjangoModelFactory):
    class Meta:
        model = Comment
    
    topic = factory.SubFactory(TopicFactory)
    author = factory.SubFactory(UserFactory)
    content = factory.Faker('text', max_nb_chars=500)