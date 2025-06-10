

import pytest
from unittest.mock import MagicMock, patch
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory


class MockRequest:
    
    def __init__(self, user=None, method='GET', data=None, files=None):
        self.user = user
        self.method = method
        self.POST = data or {}
        self.GET = data or {}
        self.FILES = files or {}
        self.session = {}
        self.COOKIES = {}
        self._messages = FallbackStorage(self)
        self.META = {'HTTP_X_REQUESTED_WITH': ''}
    
    def build_absolute_uri(self, location=None):
        return f"http://testserver{location or ''}"


@pytest.fixture
def mock_request_factory():
    def _create_request(user=None, method='GET', **kwargs):
        return MockRequest(user=user, method=method, **kwargs)
    return _create_request


@pytest.fixture
def mock_logger():
    with patch('users.views.logger') as mock_log:
        yield mock_log


@pytest.fixture
def mock_file_operations():
    with patch('users.views.os.remove') as mock_remove, \
         patch('users.views.os.path.isfile') as mock_isfile:
        mock_isfile.return_value = True
        yield {
            'remove': mock_remove,
            'isfile': mock_isfile
        }


@pytest.fixture
def mock_user_creation_form():
    with patch('users.views.CustomUserCreationForm') as mock_form:
        yield mock_form


@pytest.fixture
def mock_authentication_form():
    with patch('users.views.CustomAuthenticationForm') as mock_form:
        yield mock_form


@pytest.fixture
def mock_user_profile_form():
    with patch('users.views.UserProfileForm') as mock_form:
        yield mock_form


class FormMockHelper:
    
    @staticmethod
    def create_valid_form_mock(save_return=None):
        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form.save.return_value = save_return or MagicMock()
        mock_form.errors = {}
        mock_form.non_field_errors.return_value = []
        return mock_form
    
    @staticmethod
    def create_invalid_form_mock(errors=None, non_field_errors=None):
        mock_form = MagicMock()
        mock_form.is_valid.return_value = False
        mock_form.errors = errors or {'field': ['Error message']}
        mock_form.non_field_errors.return_value = non_field_errors or ['General error']
        return mock_form


@pytest.fixture
def form_mock_helper():
    return FormMockHelper


class DatabaseMockHelper:
    
    @staticmethod
    def mock_queryset(items=None):
        mock_qs = MagicMock()
        mock_qs.filter.return_value = mock_qs
        mock_qs.exclude.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.distinct.return_value = mock_qs
        mock_qs.__iter__ = lambda x: iter(items or [])
        mock_qs.__len__ = lambda x: len(items or [])
        mock_qs.__getitem__ = lambda x, key: (items or [])[key]
        return mock_qs


@pytest.fixture
def db_mock_helper():
    return DatabaseMockHelper


def mock_view_dependencies(**mocks):
    def decorator(test_func):
        def wrapper(*args, **kwargs):
            with patch.multiple('users.views', **mocks):
                return test_func(*args, **kwargs)
        return wrapper
    return decorator


# Контекстні менеджери для мокування
class MockFileSystem:
    
    def __init__(self, file_exists=True, remove_succeeds=True):
        self.file_exists = file_exists
        self.remove_succeeds = remove_succeeds
    
    def __enter__(self):
        self.isfile_patch = patch('users.views.os.path.isfile')
        self.remove_patch = patch('users.views.os.remove')
        
        self.mock_isfile = self.isfile_patch.start()
        self.mock_remove = self.remove_patch.start()
        
        self.mock_isfile.return_value = self.file_exists
        if not self.remove_succeeds:
            self.mock_remove.side_effect = OSError("Permission denied")
        
        return {
            'isfile': self.mock_isfile,
            'remove': self.mock_remove
        }
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.isfile_patch.stop()
        self.remove_patch.stop()


@pytest.fixture
def mock_filesystem():
    return MockFileSystem


# Спеціальні assertion функції
def assert_redirects_to_login(response):
    assert response.status_code == 302
    assert '/login/' in response.url or 'login' in response.url


def assert_has_messages(response, message_types=None):
    from django.contrib.messages import get_messages
    messages = list(get_messages(response.wsgi_request))
    assert len(messages) > 0
    
    if message_types:
        message_tags = [str(msg.tags) for msg in messages]
        for msg_type in message_types:
            assert msg_type in message_tags


@pytest.fixture
def test_assertions():
    return {
        'redirects_to_login': assert_redirects_to_login,
        'has_messages': assert_has_messages
    }


# Мок для JSON запитів
class JSONResponseMock:
    
    def __init__(self, data, status_code=200):
        self.data = data
        self.status_code = status_code
        self.content = self._encode_content()
    
    def _encode_content(self):
        import json
        return json.dumps(self.data).encode('utf-8')
    
    def json(self):
        return self.data


@pytest.fixture
def json_response_mock():
    return JSONResponseMock