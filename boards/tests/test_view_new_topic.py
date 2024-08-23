from django.contrib.auth.models import User
from django.urls import reverse, resolve
from django.test import TestCase
from ..views import new_topic
from ..forms import TopicForm
from ..models import Board, Topic, Post


class LoginRequiredNewTopicTests(TestCase):

    def setUp(self):
        default_user = User.objects.create_user(
            username="default_user", email="default_user@howdiweb.nl", password="123"
        )
        self.board = Board.objects.create(
            name="Django", description="Django board", owner=default_user
        )

    def test_template_does_not_contain_new_topic(self):
        url = reverse("board_topics", kwargs={"board_pk": self.board.pk})
        response = self.client.get(url)
        self.assertNotContains(response, "New topic")

    def test_redirection(self):
        "safeguard in case template has link to new_topic"
        login_url = reverse("login")
        url = reverse("new_topic", kwargs={"board_pk": self.board.pk})
        response = self.client.get(url)
        self.assertRedirects(response, f"{login_url}?next={url}")


class NewTopicTests(TestCase):

    def setUp(self):
        default_user = User.objects.create_user(
            username="default_user", email="default_user@howdiweb.nl", password="123"
        )
        self.board = Board.objects.create(
            name="Django", description="Django board", owner=default_user
        )
        _ = User.objects.create_user(
            username="john", email="john@doe.com", password="123"
        )
        self.client.login(username="john", password="123")

    def test_template_contains_new_topic(self):
        url = reverse("board_topics", kwargs={"board_pk": self.board.pk})
        response = self.client.get(url)
        self.assertContains(response, "New topic")

    def test_new_topic_view_success_status_code(self):
        url = reverse("new_topic", kwargs={"board_pk": self.board.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_new_topic_view_not_found_status_code(self):
        url = reverse("new_topic", kwargs={"board_pk": 99})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_new_topic_url_resolves_new_topic_view(self):
        view = resolve("/boards/1/new/")
        self.assertEqual(view.func, new_topic)

    def test_new_topic_view_contains_link_back_to_board_topics_view(self):
        new_topic_url = reverse("new_topic", kwargs={"board_pk": self.board.pk})
        board_topics_url = reverse("board_topics", kwargs={"board_pk": self.board.pk})
        response = self.client.get(new_topic_url)
        self.assertContains(response, f'href="{board_topics_url}"')

    def test_csrf(self):
        url = reverse("new_topic", kwargs={"board_pk": self.board.pk})
        response = self.client.get(url)
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_contains_form(self):
        url = reverse("new_topic", kwargs={"board_pk": self.board.pk})
        response = self.client.get(url)
        form = response.context.get("form1")
        self.assertIsInstance(form, TopicForm)

    def test_new_topic_valid_post_data(self):
        url = reverse("new_topic", kwargs={"board_pk": self.board.pk})
        data = {
            "topic_subject": "New topic",
            "post_subject": "Qude vadem temple",
            "message": "Lorem ipsum dolor sit amet",
        }
        self.client.post(url, data)
        self.assertTrue(Topic.objects.exists())
        self.assertTrue(Post.objects.exists())

    def test_new_topic_invalid_post_data(self):
        """
        Invalid post data should not redirect
        The expected behavior is to show the form again with validation errors
        """
        url = reverse("new_topic", kwargs={"board_pk": self.board.pk})
        response = self.client.post(url, {})
        form = response.context.get("form1")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(form.errors)

    def test_new_topic_invalid_post_data_empty_fields(self):
        """
        Invalid post data should not redirect
        The expected behavior is to show the form again with validation errors
        """
        url = reverse("new_topic", kwargs={"board_pk": self.board.pk})
        data = {"subject": "", "message": ""}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Topic.objects.exists())
        self.assertFalse(Post.objects.exists())
