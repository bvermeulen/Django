from django.urls import path
from boards import views

urlpatterns = [
    path("boards/", views.BoardListView.as_view(), name="boards"),
    path(
        "boards/<int:board_pk>/topics/",
        views.TopicListView.as_view(),
        name="board_topics",
    ),
    path("", views.my_boards, name="my_boards"),
    path("boards/<int:board_pk>/new/", views.new_topic, name="new_topic"),
    path(
        "boards/<int:board_pk>/topics/<int:topic_pk>/posts/",
        views.PostListView.as_view(),
        name="topic_posts",
    ),
    path(
        "boards/<int:board_pk>/topics/<int:topic_pk>/add/",
        views.add_post_to_topic,
        name="add_to_topic",
    ),
    path(
        "boards/<int:board_pk>/topics/<int:topic_pk>/posts/<int:post_pk>/edit/",
        views.PostUpdateView.as_view(),
        name="edit_post",
    ),
]
