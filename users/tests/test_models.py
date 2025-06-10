import pytest
from django.contrib.auth.models import User
from users.models import UserProfile
from forums.models import Tag

@pytest.mark.django_db
def test_user_profile_str_method():
    user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
    profile = user.userprofile
    assert str(profile) == "testuser"

@pytest.mark.django_db
def test_user_profile_created_on_user_creation():
    user = User.objects.create_user(username="testuser2", email="test2@example.com", password="password123")
    assert hasattr(user, 'userprofile')
    assert user.userprofile.email == "test2@example.com"

@pytest.mark.django_db
def test_user_profile_interests_many_to_many():
    user = User.objects.create_user(username="testuser3", email="test3@example.com", password="password123")
    tag1 = Tag.objects.create(name="Python")
    tag2 = Tag.objects.create(name="Django")

    profile = user.userprofile
    profile.interests.add(tag1, tag2)

    interests = profile.interests.all()
    assert tag1 in interests
    assert tag2 in interests
    assert interests.count() == 2
