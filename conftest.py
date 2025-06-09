import os
import sys
import django
from django.conf import settings
import pytest

project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatterchums.settings')

def pytest_configure(config):
    settings.DEBUG = False
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
    django.setup()


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass


@pytest.fixture
def mock_render(monkeypatch):
    from django.http import HttpResponse
    
    def _mock_render(request, template_name, context=None, *args, **kwargs):
        return HttpResponse(f"Rendered: {template_name}")
    
    monkeypatch.setattr('django.shortcuts.render', _mock_render)
    return _mock_render