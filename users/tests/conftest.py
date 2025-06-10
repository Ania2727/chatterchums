import pytest
import tempfile
import shutil
import io
from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

import factories


# Увімкнення доступу до БД автоматично для всіх тестів
@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass


# Django test client
@pytest.fixture
def client():
    return Client()


# Користувач і логін
@pytest.fixture
def user():
    return factories.UserFactory(username="testuser", email="test@example.com", password="testpass123")


@pytest.fixture
def authenticated_user(client, user):
    client.login(username="testuser", password="testpass123")
    return user


@pytest.fixture
def authenticated_client(client, user):
    client.login(username="testuser", password="testpass123")
    return client


# Фабрики — повертають класи фабрик
@pytest.fixture
def user_profile_factory():
    return factories.UserProfileFactory


@pytest.fixture
def tag_factory():
    return factories.TagFactory


@pytest.fixture
def forum_factory():
    return factories.ForumFactory


@pytest.fixture
def topic_factory():
    return factories.TopicFactory


@pytest.fixture
def comment_factory():
    return factories.CommentFactory


# Збір усіх фабрик (для параметризації або пакетного використання)
@pytest.fixture
def all_factories():
    return {
        "user": factories.UserFactory,
        "profile": factories.UserProfileFactory,
        "tag": factories.TagFactory,
        "forum": factories.ForumFactory,
        "topic": factories.TopicFactory,
        "comment": factories.CommentFactory,
    }


# Прикладові теги
@pytest.fixture
def sample_tags(tag_factory):
    names = ['Python', 'Django', 'JavaScript', 'React', 'DevOps']
    return [tag_factory(name=name) for name in names]


# Форум з темами та коментарями
@pytest.fixture
def sample_forum_with_data(forum_factory, topic_factory, comment_factory, user):
    forum = forum_factory(creator=user, title="Test Forum")
    topics = []
    for i in range(3):
        topic = topic_factory(forum=forum, author=user, title=f"Topic {i+1}")
        topics.append(topic)
        for j in range(2):
            comment_factory(topic=topic, author=user, content=f"Comment {j+1} on Topic {i+1}")
    return forum, topics


# Тимчасова директорія для MEDIA_ROOT
@pytest.fixture
def temp_media_root(settings):
    temp_dir = tempfile.mkdtemp()
    settings.MEDIA_ROOT = temp_dir
    yield temp_dir
    shutil.rmtree(temp_dir)


# Мок-зображення
@pytest.fixture
def mock_image_file():
    def _create(name="test.jpg", size=(100, 100), color='red'):
        file = io.BytesIO()
        image = Image.new('RGB', size, color)
        image.save(file, 'JPEG')
        file.seek(0)
        return SimpleUploadedFile(name, file.read(), content_type='image/jpeg')
    return _create


# Моки для логування та файлової системи
@pytest.fixture
def mock_logging(mocker):
    return mocker.patch('users.views.logger')


@pytest.fixture
def mock_os_remove(mocker):
    return mocker.patch('os.remove')


@pytest.fixture
def mock_os_path_isfile(mocker):
    return mocker.patch('os.path.isfile', return_value=True)


# Додаткові фікстури для тестування
@pytest.fixture
def user_with_profile(user):
    """Користувач з гарантованим профілем"""
    # Профіль повинен створюватися автоматично через сигнал
    # але якщо ні, створюємо явно
    from users.models import UserProfile
    profile, created = UserProfile.objects.get_or_create(user=user)
    return user, profile


@pytest.fixture
def multiple_users():
    """Створює кілька користувачів для тестів"""
    users = []
    for i in range(5):
        user = factories.UserFactory(
            username=f"user{i}",
            email=f"user{i}@example.com",
            password="testpass123"
        )
        users.append(user)
    return users


@pytest.fixture
def forum_with_members(user, multiple_users):
    """Форум з кількома учасниками"""
    forum = factories.ForumFactory(creator=user)
    for member_user in multiple_users[:3]:
        forum.members.add(member_user)
    return forum


@pytest.fixture
def topic_with_comments(user):
    """Тема з коментарями"""
    topic = factories.TopicFactory(author=user)
    comments = []
    for i in range(5):
        comment = factories.CommentFactory(topic=topic, author=user)
        comments.append(comment)
    return topic, comments


@pytest.fixture
def session_with_data(client):
    """Клієнт з даними в сесії"""
    session = client.session
    session['recommended_forums'] = [
        {
            'id': 1,
            'title': 'Test Forum',
            'description': 'Test Description',
            'common_keywords': ['test'],
            'match_score': 1
        }
    ]
    session.save()
    return client


# Фікстури для різних типів запитів
@pytest.fixture
def ajax_client(client):
    """Клієнт для AJAX запитів"""
    def _make_request(method, url, data=None, **kwargs):
        kwargs['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        if method.upper() == 'GET':
            return client.get(url, data, **kwargs)
        elif method.upper() == 'POST':
            return client.post(url, data, **kwargs)
    return _make_request


@pytest.fixture
def json_client(client):
    """Клієнт для JSON запитів"""
    def _post_json(url, data):
        import json
        return client.post(
            url,
            json.dumps(data),
            content_type='application/json'
        )
    return _post_json


# Мок об'єкти для форм
@pytest.fixture
def mock_form_valid(mocker):
    """Мок для валідної форми"""
    mock_form = mocker.MagicMock()
    mock_form.is_valid.return_value = True
    mock_form.save.return_value = mocker.MagicMock()
    mock_form.errors = {}
    mock_form.non_field_errors.return_value = []
    return mock_form


@pytest.fixture
def mock_form_invalid(mocker):
    """Мок для невалідної форми"""
    mock_form = mocker.MagicMock()
    mock_form.is_valid.return_value = False
    mock_form.errors = {'email': ['Invalid email format']}
    mock_form.non_field_errors.return_value = ['General form error']
    return mock_form


# Фікстури для тестування файлів
@pytest.fixture
def test_image_data():
    """Дані тестового зображення"""
    file = io.BytesIO()
    image = Image.new('RGB', (100, 100), 'blue')
    image.save(file, 'JPEG')
    file.seek(0)
    return file.read()


@pytest.fixture
def uploaded_file(test_image_data):
    """Завантажений файл для тестів"""
    return SimpleUploadedFile(
        "test.jpg",
        test_image_data,
        content_type="image/jpeg"
    )


# Фікстури для налаштувань
@pytest.fixture
def override_settings(settings):
    """Зміна налаштувань для тестів"""
    def _override(**kwargs):
        for key, value in kwargs.items():
            setattr(settings, key, value)
    return _override


# Фікстури для URL-ів
@pytest.fixture
def url_names():
    """Словник з іменами URL-ів"""
    return {
        'profile': 'users:profile',
        'delete_profile': 'users:delete_profile',
        'settings': 'users:settings',
        'logout': 'users:logout',
        'signup': 'users:signup',
        'login': 'users:login',
        'quiz': 'users:quiz',
        'explore': 'users:explore',
        'save_interests': 'users:save_interests',
        'forum_recommendations': 'users:forum_recommendations',
        'edit_profile': 'users:edit_profile',
        'home': 'home',
    }


@pytest.fixture
def reverse_url(url_names):
    """Функція для отримання URL за іменем"""
    def _reverse(name, *args, **kwargs):
        return reverse(url_names[name], *args, **kwargs)
    return _reverse