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
    path('edit/', edit_profile_view, name='edit_profile'),
    path('admin-panel/', admin_panel_view, name='admin_panel'),
    path('add-tag/', add_tag, name='add_tag'),
    path('edit-tag/<int:tag_id>/', edit_tag, name='edit_tag'),
    path('delete-tag/<int:tag_id>/', delete_tag, name='delete_tag'),
    path('list-tags/', list_tags, name='list_tags'),
    path('list-users/', list_users, name='list_users'),
    path('promote-moderator/<int:user_id>/', promote_to_moderator, name='promote_moderator'),
    path('promote-admin/<int:user_id>/', promote_to_admin, name='promote_admin'),
    path('remove-moderator/<int:user_id>/', remove_moderator, name='remove_moderator'),
    path('remove-admin/<int:user_id>/', remove_admin, name='remove_admin'),
    path('management-stats/', management_stats, name='management_stats'),
    path('search-users/', search_users, name='search_users'),
    path('profile/<int:user_id>/', view_user_profile, name='view_profile'),
    path('password/', change_password, name='change_password'),
    path('password/done/', change_password_done, name='change_password_done'),
    path('forum-statistics', forum_statistics, name='forum_statistics'),
    path('admin-panel/complaints/', admin_complaints_view, name='admin_complaints'),

]