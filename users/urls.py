from django.urls import path
from .views import *

app_name = 'users' 

urlpatterns = [
    path('signup/', signup_view, name='signup'),
    path('login/', login_view, name='login'),
    path('profile/', profile_view, name='profile'),
    path('delete/', delete_profile, name='delete_profile'),
    path('logout/', logout_view, name='logout'),
    path('quiz/', quiz_view, name='quiz'),
    path('explore/', explore_view, name='explore'),
    path('settings/', settings_view, name='settings'),
    path('save-interests/', save_interests, name='save_interests'),
    path('forum-recommendations/', forum_recommendations, name='forum-recommendations'),
    path('edit/', edit_profile_view, name='edit_profile')
]