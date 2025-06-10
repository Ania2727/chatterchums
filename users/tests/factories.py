# users/tests/factories.py
import factory
from factory.django import DjangoModelFactory
from django.contrib.auth.models import User
from users.models import UserProfile
from forums.models import Forum, Topic, Comment, Tag
from django.core.files.base import ContentFile
from PIL import Image
import io


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.set_password(extracted)
        else:
            self.set_password('defaultpass123')
        self.save()


class UserProfileFactory(DjangoModelFactory):
    class Meta:
        model = UserProfile

    user = factory.SubFactory(UserFactory)
    email = factory.LazyAttribute(lambda obj: obj.user.email)
    bio = factory.Faker('text', max_nb_chars=200)

    @factory.post_generation
    def interests(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for interest in extracted:
                self.interests.add(interest)

    @factory.lazy_attribute
    def profile_pic(self):
        file = io.BytesIO()
        image = Image.new('RGB', (100, 100), 'red')
        image.save(file, 'JPEG')
        file.seek(0)
        return ContentFile(file.read(), 'test.jpg')


class TagFactory(DjangoModelFactory):
    class Meta:
        model = Tag

    name = factory.Sequence(lambda n: f'tag_{n}')


class ForumFactory(DjangoModelFactory):
    class Meta:
        model = Forum
        skip_postgeneration_save = True

    title = factory.Faker('sentence', nb_words=4)
    description = factory.Faker('text', max_nb_chars=200)
    creator = factory.SubFactory(UserFactory)
    # Видаляємо created_at, оскільки його немає в моделі Forum

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for tag in extracted:
                self.tags.add(tag)

    @factory.post_generation
    def members(self, create, extracted, **kwargs):
        if not create:
            return
        self.members.add(self.creator)
        if extracted:
            for member in extracted:
                self.members.add(member)


class TopicFactory(DjangoModelFactory):
    class Meta:
        model = Topic

    title = factory.Faker('sentence', nb_words=6)
    content = factory.Faker('text', max_nb_chars=500)
    author = factory.SubFactory(UserFactory)
    forum = factory.SubFactory(ForumFactory)
    created_at = factory.Faker('date_time_this_year')
    views = factory.Faker('random_int', min=0, max=1000)
    is_pinned = False


class CommentFactory(DjangoModelFactory):
    class Meta:
        model = Comment

    content = factory.Faker('text', max_nb_chars=300)
    author = factory.SubFactory(UserFactory)
    topic = factory.SubFactory(TopicFactory)
    created_at = factory.Faker('date_time_this_year')

    @factory.post_generation
    def upvotes(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for user in extracted:
                self.upvotes.add(user)

    @factory.post_generation
    def downvotes(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for user in extracted:
                self.downvotes.add(user)


# ------------------
# Utility functions
# ------------------

def create_user_with_profile(**kwargs):
    """Створює користувача та його профіль, повертає пару (user, userprofile)."""
    user = UserFactory(**kwargs)
    # UserProfile буде створено автоматично завдяки сигналу, або створимо явно:
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return user, profile


def create_forum_with_topics(num_topics=3, **forum_kwargs):
    forum = ForumFactory(**forum_kwargs)
    topics = [TopicFactory(forum=forum) for _ in range(num_topics)]
    return forum, topics


def create_topic_with_comments(num_comments=5, **topic_kwargs):
    topic = TopicFactory(**topic_kwargs)
    comments = [CommentFactory(topic=topic) for _ in range(num_comments)]
    return topic, comments


def create_test_image(name='test.jpg', size=(100, 100), color='blue', format='JPEG'):
    file = io.BytesIO()
    image = Image.new('RGB', size, color)
    image.save(file, format)
    file.seek(0)
    return ContentFile(file.read(), name)