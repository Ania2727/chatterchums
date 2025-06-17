import pytest
import json
from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from unittest.mock import patch, MagicMock
from users.models import UserProfile
from forums.models import Forum, Topic, Comment, Tag
import factories




class TestAuthentication:
    
    def test_signup_flow(self, client):
        response = client.get(reverse('users:signup'))
        assert response.status_code == 200
        assert 'form' in response.context
        
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'testpass123!',
            'password2': 'testpass123!'
        }
        response = client.post(reverse('users:signup'), data)
        assert response.status_code == 302
        assert response.url == reverse('users:quiz')
        assert User.objects.filter(username='newuser').exists()
    
    def test_login_flow(self, client, user):
        response = client.get(reverse('users:login'))
        assert response.status_code == 200
        
        data = {'username': 'testuser', 'password': 'testpass123'}
        response = client.post(reverse('users:login'), data)
        assert response.status_code == 302
        assert response.url == reverse('users:profile')
        
        data['remember_me'] = 'on'
        response = client.post(reverse('users:login'), data)
        session = client.session
        assert session.get_expiry_age() == 1209600
    
    def test_logout(self, authenticated_client):
        response = authenticated_client.get(reverse('users:logout'))
        assert response.status_code == 302
        assert response.url == reverse('home')


class TestProfileManagement:
    
    def test_profile_view(self, authenticated_client, user):
        response = authenticated_client.get(reverse('users:profile'))
        assert response.status_code == 200
    
    def test_edit_profile_basic(self, authenticated_client, user):
        response = authenticated_client.get(reverse('users:edit_profile'))
        assert response.status_code == 200
        assert 'form' in response.context
        
        data = {
            'bio': 'Updated bio text',
            'email': 'updated@example.com'
        }
        response = authenticated_client.post(reverse('users:edit_profile'), data)
        assert response.status_code == 302
        assert response.url == reverse('users:profile')
        
        user.userprofile.refresh_from_db()
        assert user.userprofile.bio == 'Updated bio text'
    
    @patch('users.views.os.remove')
    @patch('users.views.os.path.isfile')
    def test_profile_picture_operations(self, mock_isfile, mock_remove,
                                      authenticated_client, user, mock_image_file):
        mock_isfile.return_value = True
        
        profile = user.userprofile
        profile.profile_pic = 'test.jpg'
        profile.save()
        
        data = {'bio': 'Test bio', 'profile_pic-clear': 'on'}
        response = authenticated_client.post(reverse('users:edit_profile'), data)
        
        assert response.status_code == 302
        profile.refresh_from_db()
        assert not profile.profile_pic
        mock_remove.assert_called()
        
        mock_remove.reset_mock()
        profile.profile_pic = 'old_test.jpg'
        profile.save()
        
        new_image = mock_image_file('new_test.jpg')
        data = {'bio': 'Test bio', 'profile_pic': new_image}
        response = authenticated_client.post(reverse('users:edit_profile'), data)
        
        assert response.status_code == 302
        mock_remove.assert_called()  # Стара картинка видалена
    
    def test_delete_profile(self, authenticated_client, user):
        response = authenticated_client.get(reverse('users:delete_profile'))
        assert response.status_code == 302
        assert response.url == reverse('users:profile')
        
        user_id = user.id
        response = authenticated_client.post(reverse('users:delete_profile'))
        assert response.status_code == 302
        assert response.url == reverse('home')
        assert not User.objects.filter(id=user_id).exists()


class TestUserExperience:
    
    def test_settings_and_themes(self, client):
        response = client.get(reverse('users:settings'))
        assert response.status_code == 200
        assert response.context['current_theme'] == 'light'
        
        response = client.get(reverse('users:settings'), {'theme': 'dark'})
        assert response.status_code == 200
        assert response.context['current_theme'] == 'dark'
        assert response.cookies['theme'].value == 'dark'
        
        response = client.get(
            reverse('users:settings'), 
            {'theme': 'dark'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True
        assert data['theme'] == 'dark'
    
    def test_quiz_and_interests(self, client, authenticated_client, user, sample_tags):
        response = client.get(reverse('users:quiz'))
        assert response.status_code == 200
        assert 'tags' in response.context
        
        data = {'interests': [sample_tags[0].id, sample_tags[1].id]}
        response = authenticated_client.post(reverse('users:save_interests'), data)
        assert response.status_code == 302
        assert response.url == reverse('users:explore')
        
        profile = user.userprofile
        assert profile.interests.count() == 2
        assert sample_tags[0] in profile.interests.all()
    
    def test_explore_recommendations(self, authenticated_client, user, sample_tags):
        profile = user.userprofile
        profile.interests.add(sample_tags[0])
        
        forum = factories.ForumFactory(title="Python Forum")
        forum.tags.add(sample_tags[0])
        
        response = authenticated_client.get(reverse('users:explore'))
        assert response.status_code == 200
        
        recommended_forums = response.context['recommended_forums']
        assert len(recommended_forums) > 0
        assert any(f['id'] == forum.id for f in recommended_forums)


class TestErrorHandling:
    
    def test_invalid_form_data(self, client):
        signup_data = {
            'username': 'newuser',
            'email': 'invalid-email',
            'password1': 'testpass123!',
            'password2': 'different_pass'
        }
        response = client.post(reverse('users:signup'), signup_data)
        assert response.status_code == 200
        assert not User.objects.filter(username='newuser').exists()
        
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) > 0
        
        login_data = {'username': 'nonexistent', 'password': 'wrongpass'}
        response = client.post(reverse('users:login'), login_data)
        assert response.status_code == 200
        
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) > 0
    
    @patch('users.views.logger')
    def test_file_operation_errors(self, mock_logger, authenticated_client, user):
        with patch('users.views.os.remove') as mock_remove, \
             patch('users.views.os.path.isfile') as mock_isfile:
            
            mock_isfile.return_value = True
            mock_remove.side_effect = Exception("Permission denied")
            
            profile = user.userprofile
            profile.profile_pic = 'test.jpg'
            profile.save()
            
            response = authenticated_client.post(reverse('users:delete_profile'))
            assert response.status_code == 302
            mock_logger.error.assert_called()


class TestIntegration:
    
    def test_complete_user_journey(self, client, sample_tags):
        # Реєстрація
        signup_data = {
            'username': 'journeyuser',
            'email': 'journey@example.com',
            'password1': 'testpass123!',
            'password2': 'testpass123!'
        }
        response = client.post(reverse('users:signup'), signup_data)
        assert response.status_code == 302
        
        login_data = {'username': 'journeyuser', 'password': 'testpass123!'}
        response = client.post(reverse('users:login'), login_data)
        assert response.status_code == 302
        
        response = client.get(reverse('users:profile'))
        assert response.status_code == 200
        
        data = {'interests': [sample_tags[0].id]}
        response = client.post(reverse('users:save_interests'), data)
        assert response.status_code == 302
        
        response = client.get(reverse('users:explore'))
        assert response.status_code == 200
        
        response = client.get(reverse('users:settings'))
        assert response.status_code == 200


@pytest.mark.parametrize("url_name", [
    'users:signup',
    'users:login',
])
def test_authenticated_user_redirects(authenticated_client, url_name):
    response = authenticated_client.get(reverse(url_name))
    assert response.status_code == 302
    assert response.url == reverse('users:profile')