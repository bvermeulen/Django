from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve, reverse
from ..forms import PostForm
from ..models import Board, Post, Topic
from ..views import add_post_to_topic


class AddToTopicTestCase(TestCase):
    """
    Base test case to be used in all `add_to_topic` view tests
    """

    def setUp(self):
        self.username = "john"
        self.password = "123"
        self.user = User.objects.create_user(
            username=self.username, email="john@doe.com", password=self.password
        )
        self.board = Board.objects.create(
            name="Django", description="Django board", owner=self.user
        )
        self.topic = Topic.objects.create(
            topic_subject="Hello, world", board=self.board, starter=self.user
        )
        Post.objects.create(
            post_subject="Lorem",
            message="Lorem ipsum dolor sit amet",
            topic=self.topic,
            created_by=self.user,
        )
        self.url = reverse(
            "add_to_topic",
            kwargs={"board_pk": self.board.pk, "topic_pk": self.topic.pk},
        )

class LoginRequiredNewTopicTests(AddToTopicTestCase):

    def test_redirection(self):
        login_url = reverse("login")
        self.response = self.client.get(self.url)
        self.assertRedirects(self.response, f"{login_url}?next={self.url}")


class AddToTopicTests(AddToTopicTestCase):
    def setUp(self):
        super().setUp()
        self.client.login(username=self.username, password=self.password)
        self.response = self.client.get(self.url)

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_view_function(self):
        view = resolve("/boards/1/topics/1/add/")
        self.assertEqual(view.func, add_post_to_topic)

    def test_csrf(self):
        self.assertContains(self.response, "csrfmiddlewaretoken")

    def test_contains_form(self):
        form = self.response.context.get("form")
        self.assertIsInstance(form, PostForm)

    def test_form_inputs(self):
        """
        The view must contain:
        <input: csrf (2x), allowed_editor, post_subject, markdown-image-upload
        <textarea: messege
        """
        self.assertContains(self.response, "<input", 5)
        self.assertContains(self.response, "<textarea", 1)


class SuccessfulAddToTopicTests(AddToTopicTestCase):
    def setUp(self):
        super().setUp()
        self.client.login(username=self.username, password=self.password)
        context = {"post_subject": "quod totem", "message": "imperfectum totibus"}
        self.response = self.client.post(self.url, context)

    def test_redirection(self):
        """
        A valid form submission should redirect the user
        """
        topic_posts_url = reverse(
            "topic_posts", kwargs={"board_pk": self.board.pk, "topic_pk": self.topic.pk}
        )
        topic_posts_url += "?page=1"
        self.assertRedirects(self.response, topic_posts_url)

    def test_add_to_created(self):
        """
        The total post count should be 2
        The one created in the `AddToTopicTestCase` setUp
        and another created by the post data in this class
        """
        self.assertEqual(Post.objects.count(), 2)


class InvalidAddToTopicTests(AddToTopicTestCase):
    def setUp(self):
        """
        Submit an empty dictionary to the `add_to_topic` view
        """
        super().setUp()
        self.client.login(username=self.username, password=self.password)
        self.response = self.client.post(self.url, {})

    def test_status_code(self):
        """
        An invalid form submission should return to the same page
        """
        self.assertEqual(self.response.status_code, 200)

    def test_form_errors(self):
        form = self.response.context.get("form")
        self.assertTrue(form.errors)
