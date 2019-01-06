from django.urls import path
from boards import views as boards_views

urlpatterns = [
    path('', boards_views.HomeListView.as_view(), name='home'),
    path('boards/', boards_views.BoardListView.as_view(), name='boards'),
    path('boards/<int:board_pk>/',
         boards_views.TopicListView.as_view(), name='board_topics'),
    path('boards/<int:board_pk>/new/',
         boards_views.new_topic, name='new_topic'),
    path('boards/<int:board_pk>/topics/<int:topic_pk>/posts/',
         boards_views.PostListView.as_view(), name='topic_posts'),
    path('boards/<int:board_pk>/topics/<int:topic_pk>/reply/',
         boards_views.reply_topic, name='reply_topic'),
    path('boards/<int:board_pk>/topics/<int:topic_pk>/posts/<int:post_pk>/edit/',
         boards_views.PostUpdateView.as_view(), name='edit_post'),
         ]
