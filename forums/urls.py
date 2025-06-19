from django.urls import path
from . import views
from .views import *

app_name = 'forums'

urlpatterns = [
    #path('', forum_list, name='forum_list.html'),
    path('', forum_list, name='forum_list'),
    path('user-forums/',user_forums, name='user_forums'),
    path('add-forum/',add_forum, name='add_forum'),
    path('<int:forum_id>/',forum_detail, name='forum_detail'),
    path('<int:forum_id>/join/',join_forum, name='join_forum'),
    path('<int:forum_id>/leave/',leave_forum, name='leave_forum'),

    path('<int:forum_id>/create-topic/',create_topic, name='create_topic'),
    path('<int:forum_id>/topic/<int:topic_id>/',topic_detail, name='topic_detail'),
    path('<int:forum_id>/topic/<int:topic_id>/edit/',edit_topic, name='edit_topic'),

    path('<int:forum_id>/topic/<int:topic_id>/add-comment/',add_comment, name='add_comment'),
    path('<int:forum_id>/topic/<int:topic_id>/comment/<int:comment_id>/edit/',edit_comment, name='edit_comment'),
    path('<int:forum_id>/topic/<int:topic_id>/comment/<int:comment_id>/delete/', delete_comment, name='delete_comment'),
    
    path('<int:forum_id>/topic/<int:topic_id>/add-comment-ajax/', add_comment_ajax, name='add_comment_ajax'),
    path('<int:forum_id>/topic/<int:topic_id>/comment/<int:comment_id>/edit-ajax/', edit_comment_ajax, name='edit_comment_ajax'),
    path('<int:forum_id>/topic/<int:topic_id>/comment/<int:comment_id>/delete-ajax/', delete_comment_ajax, name='delete_comment_ajax'),

    path('forums/<int:forum_id>/edit/', views.edit_forum, name='edit_forum'),
    path('forums/<int:forum_id>/delete/', views.delete_forum, name='delete_forum'),

    path('complaints/submit/', views.submit_complaint_ajax, name='submit_complaint_ajax'),
    path('<int:forum_id>/report/', views.report_forum, name='report_forum'),


]