from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve, reverse
from ..models import Board, Post, Topic
from ..views import PostListView


class TopicPostsTests(TestCase):
    def setUp(self):
        default_user = User.objects.create_user(
            username="default_user", email="default_user@howdiweb.nl", password="123"
        )
        username = "joe"
        password = "123"
        _ = User.objects.create_user(
            username=username, email="joe@email.com", password=password
        )
        self.client.login(username=username, password=password)
        board = Board.objects.create(
            name="Django", description="Django board", owner=default_user
        )
        topic = Topic.objects.create(
            topic_subject="Hello, world", board=board, starter=default_user
        )
        Post.objects.create(
            post_subject="Quod io",
            message="Lorem ipsum dolor sit amet",
            topic=topic,
            created_by=default_user,
        )
        self.context = {"board_pk": board.pk, "topic_pk": topic.pk}
        url = reverse("topic_posts", kwargs=self.context)
        self.response = self.client.get(url)

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_view_function(self):
        view = resolve("/boards/1/topics/1/posts/")
        self.assertEqual(view.func.view_class, PostListView)

    def test_template_contains_add_to_topic(self):
        self.assertContains(self.response, "Add to topic")

    def test_template_does_not_contain_add_to_topic(self):
        self.client.logout()
        url = reverse("topic_posts", kwargs=self.context)
        response = self.client.get(url)
        self.assertNotContains(response, "Add to topic")

    def test_redirection(self):
        " safeguard in case template incorrectly has the link to add_to_topic"
        self.client.logout()
        login_url = reverse('login')
        url = reverse('add_to_topic', kwargs=self.context)
        response = self.client.get(url)
        self.assertRedirects(response, f'{login_url}?next={url}')
