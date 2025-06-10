import pytest
from django.contrib.auth.models import User
from users.forms import CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm
from users.models import UserProfile

@pytest.mark.django_db
def test_valid_custom_user_creation_form():
    form_data = {
        'email': 'test@example.com',
        'username': 'testuser',
        'password1': 'strongpassword123',
        'password2': 'strongpassword123',
    }
    form = CustomUserCreationForm(data=form_data)
    assert form.is_valid()
    user = form.save()
    assert user.email == 'test@example.com'
    assert User.objects.filter(username='testuser').exists()

@pytest.mark.django_db
def test_invalid_custom_user_creation_email_exists():
    User.objects.create_user(username='existing', email='existing@example.com', password='12345')
    form_data = {
        'email': 'existing@example.com',
        'username': 'newuser',
        'password1': 'strongpassword123',
        'password2': 'strongpassword123',
    }
    form = CustomUserCreationForm(data=form_data)
    assert not form.is_valid()
    assert 'email' in form.errors

@pytest.mark.django_db
def test_invalid_custom_user_creation_password_mismatch():
    form_data = {
        'email': 'unique@example.com',
        'username': 'uniqueuser',
        'password1': 'password123',
        'password2': 'password456',
    }
    form = CustomUserCreationForm(data=form_data)
    assert not form.is_valid()
    assert 'password2' in form.errors

def test_valid_custom_authentication_form():
    form_data = {
        'username': 'user123',
        'password': 'secret123',
    }
    form = CustomAuthenticationForm(data=form_data)
    assert form.fields['username'].widget.attrs['placeholder'] == 'username'
    assert form.fields['password'].widget.attrs['placeholder'] == 'password'

@pytest.mark.django_db
def test_valid_user_profile_form():
    form_data = {
        'bio': 'This is a test bio.',
    }
    form = UserProfileForm(data=form_data)
    assert form.is_valid()
