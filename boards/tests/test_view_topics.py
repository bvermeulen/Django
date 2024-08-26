from django.contrib.auth.models import User
from django.urls import reverse, resolve
from django.test import TestCase
from ..models import Board, Topic, Post
from ..views import TopicListView


class TopicsTestsNoLogin(TestCase):

    def setUp(self):
        default_user = User.objects.create_user(
            username="default_user", email="default_user@howdiweb.nl", password="123"
        )
        self.default_board = Board.objects.create(
            name="Django", description="Django board", owner=default_user
        )
        self.topic = Topic.objects.create(
            topic_subject="Hello, world", board=self.default_board, starter=default_user
        )
        Post.objects.create(
            post_subject="Lorem",
            message="Lorem ipsum dolor sit amet",
            topic=self.topic,
            created_by=default_user,
        )
        joe = User.objects.create(username="joe", email="joe@doe.com", password="456")
        joe_board = Board.objects.create(name="Joe", description="Joe board", owner=joe)
        joe_topic = Topic.objects.create(
            topic_subject="Hello Joe", board=joe_board, starter=joe
        )
        Post.objects.create(
            post_subject="Je suis",
            message="mon nom est joe",
            topic=joe_topic,
            created_by=joe,
        )

    def get_response(self):
        url = reverse("board_topics", kwargs={"board_pk": self.default_board.pk})
        return self.client.get(url)

    def test_csrf(self):
        self.assertContains(self.get_response(), "csrfmiddlewaretoken")

    def test_topics_view_not_found_status_code(self):
        url = reverse("board_topics", kwargs={"board_pk": 99})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_topics_view_success_status_code(self):
        response = self.get_response()
        self.assertEqual(response.status_code, 200)

    def test_topics_url_resolves_board_topics_view(self):
        view = resolve("/boards/1/topics/")
        self.assertEqual(view.func.view_class, TopicListView)

    def test_topics_view_contains_link_back_to_boardpage(self):
        boardpage_url = reverse("boards")
        response = self.get_response()
        self.assertContains(response, f'href="{boardpage_url}"')

    def test_template_does_not_contain_new_topic(self):
        response = self.get_response()
        self.assertNotContains(response, "New topic")

    def test_new_topic_redirection(self):
        "safeguard in case template has link to new_topic"
        new_topic_url = reverse("new_topic", kwargs={"board_pk": self.default_board.pk})
        login_url = reverse("login")
        response = self.client.get(new_topic_url)
        self.assertRedirects(response, f"{login_url}?next={new_topic_url}")

    def test_template_does_not_contain_contributors_rename_board(self):
        response = self.get_response()
        self.assertNotContains(response, "Contributors")
        self.assertNotContains(response, "Rename board")

    def test_template_contains_link_to_default_topic_only(self):
        response = self.get_response()
        topics = response.context_data["topics"]
        self.assertEqual(len(topics), 1)
        topics_url = reverse(
            "topic_posts",
            kwargs={"board_pk": self.default_board.pk, "topic_pk": self.topic.pk},
        )
        self.assertContains(response, f'href="{topics_url}"')


class DefaultTopicsTestsUserLogin(TestCase):

    def setUp(self):
        default_user = User.objects.create_user(
            username="default_user", email="default_user@howdiweb.nl", password="123"
        )
        self.default_board = Board.objects.create(
            name="Django", description="Django board", owner=default_user
        )
        self.topic = Topic.objects.create(
            topic_subject="Hello, world", board=self.default_board, starter=default_user
        )
        Post.objects.create(
            post_subject="Lorem",
            message="Lorem ipsum dolor sit amet",
            topic=self.topic,
            created_by=default_user,
        )
        joe = User.objects.create_user(
            username="joe", email="joe@doe.com", password="456"
        )
        joe_board = Board.objects.create(name="Joe", description="Joe board", owner=joe)
        joe_topic = Topic.objects.create(
            topic_subject="Hello Joe", board=joe_board, starter=joe
        )
        Post.objects.create(
            post_subject="Je suis",
            message="mon nom est joe",
            topic=joe_topic,
            created_by=joe,
        )
        self.client.login(username="joe", password="456")

    def get_response(self):
        url = reverse("board_topics", kwargs={"board_pk": self.default_board.pk})
        return self.client.get(url)

    def test_topics_view_contains_navigation_links(self):
        new_topic_url = reverse("new_topic", kwargs={"board_pk": self.default_board.pk})
        response = self.get_response()
        self.assertContains(response, f'href="{new_topic_url}"')

    def test_template_contains_new_topic(self):
        response = self.get_response()
        self.assertContains(response, "New topic")

    def test_template_does_not_contain_contributors_rename_board(self):
        response = self.get_response()
        self.assertNotContains(response, "Contributors")
        self.assertNotContains(response, "Rename board")

    def test_template_contains_link_to_default_topic_only(self):
        response = self.get_response()
        topics = response.context_data["topics"]
        self.assertEqual(topics.count(), 1)
        topics_url = reverse(
            "topic_posts",
            kwargs={"board_pk": self.default_board.pk, "topic_pk": self.topic.pk},
        )
        self.assertContains(response, f'href="{topics_url}"')


class UserTopicsTests(TestCase):

    def setUp(self):
        default_user = User.objects.create_user(
            username="default_user", email="default_user@howdiweb.nl", password="123"
        )
        default_board = Board.objects.create(
            name="Django", description="Django board", owner=default_user
        )
        self.topic = Topic.objects.create(
            topic_subject="Hello, world", board=default_board, starter=default_user
        )
        Post.objects.create(
            post_subject="Lorem",
            message="Lorem ipsum dolor sit amet",
            topic=self.topic,
            created_by=default_user,
        )
        joe = User.objects.create_user(
            username="joe", email="joe@doe.com", password="456"
        )
        self.joe_board = Board.objects.create(
            name="Joe", description="Joe board", owner=joe
        )
        self.joe_topic = Topic.objects.create(
            topic_subject="Hello Joe", board=self.joe_board, starter=joe
        )
        Post.objects.create(
            post_subject="Je suis",
            message="mon nom est joe",
            topic=self.joe_topic,
            created_by=joe,
        )
        User.objects.create_user(username="jane", email="jane@doe.com", password="789")
        self.client.login(username="joe", password="456")

    def get_response(self):
        url = reverse("board_topics", kwargs={"board_pk": self.joe_board.pk})
        return self.client.get(url)

    def post_response(self, data):
        url = reverse("board_topics", kwargs={"board_pk": self.joe_board.pk})
        return self.client.post(url, data)

    def test_topics_view_contains_navigation_links(self):
        new_topic_url = reverse("new_topic", kwargs={"board_pk": self.joe_board.pk})
        response = self.get_response()
        self.assertContains(response, f'href="{new_topic_url}"')

    def test_template_contains_new_topic(self):
        response = self.get_response()
        self.assertContains(response, "New topic")

    def test_template_contains_contributors_rename_board(self):
        response = self.get_response()
        self.assertContains(response, "Contributors")
        self.assertContains(response, "Rename board")

    def test_template_does_not_contain_delete(self):
        response = self.get_response()
        self.assertNotContains(response, "Delete board")

    def test_template_contains_delete_when_empty(self):
        self.joe_topic.delete()
        response = self.get_response()
        self.assertContains(response, "Delete board")

    def test_contributors_board(self):
        data = {"name": "Joe", "description": "Joe board", "contributor": [3]}
        self.post_response(data)
        response = self.get_response()
        board = response.context_data["board"]
        self.assertEqual(board.contributor.first().username, "jane")

    def test_rename_board(self):
        data = {
            "name": "Joe",
            "description": "Joe board",
            "new_board_name": "New name board Joe",
        }
        self.post_response(data)
        response = self.get_response()
        board = response.context_data["board"]
        self.assertEqual(board.name, "New name board Joe")

    def test_delete_board(self):
        self.assertEqual(Board.objects.count(), 2)
        self.joe_topic.delete()
        data = {"name": "Joe", "description": "Joe board", "delete_btn": "delete_board"}
        response = self.post_response(data)
        self.assertRedirects(response, reverse("boards"))
        self.assertEqual(Board.objects.count(), 1)

    def test_template_contains_link_to_user_topic_only(self):
        response = self.get_response()
        topics = response.context_data["topics"]
        self.assertEqual(topics.count(), 1)
        topics_url = reverse(
            "topic_posts",
            kwargs={"board_pk": self.joe_board.pk, "topic_pk": self.joe_topic.pk},
        )
        self.assertContains(response, f'href="{topics_url}"')


class OtherUserTopicsTests(TestCase):

    def setUp(self):
        default_user = User.objects.create_user(
            username="default_user", email="default_user@howdiweb.nl", password="123"
        )
        default_board = Board.objects.create(
            name="Django", description="Django board", owner=default_user
        )
        self.topic = Topic.objects.create(
            topic_subject="Hello, world", board=default_board, starter=default_user
        )
        Post.objects.create(
            post_subject="Lorem",
            message="Lorem ipsum dolor sit amet",
            topic=self.topic,
            created_by=default_user,
        )
        joe = User.objects.create_user(
            username="joe", email="joe@doe.com", password="456"
        )
        jane = User.objects.create_user(
            username="jane", email="jane@doe.com", password="789"
        )
        self.joe_board = Board.objects.create(
            name="Joe", description="Joe board", owner=joe
        )
        self.joe_board.contributor.add(jane)
        self.joe_topic = Topic.objects.create(
            topic_subject="Hello Joe", board=self.joe_board, starter=joe
        )
        Post.objects.create(
            post_subject="Je suis",
            message="mon nom est joe",
            topic=self.joe_topic,
            created_by=joe,
        )
        self.client.login(username="jane", password="789")

    def get_response(self):
        url = reverse("board_topics", kwargs={"board_pk": self.joe_board.pk})
        return self.client.get(url)

    def post_response(self, data):
        url = reverse("board_topics", kwargs={"board_pk": self.joe_board.pk})
        return self.client.post(url, data)

    def test_topics_view_contains_navigation_links(self):
        new_topic_url = reverse("new_topic", kwargs={"board_pk": self.joe_board.pk})
        response = self.get_response()
        self.assertContains(response, f'href="{new_topic_url}"')

    def test_template_contains_new_topic(self):
        response = self.get_response()
        self.assertContains(response, "New topic")

    def test_template_does_not_contain_contributors_rename_board(self):
        response = self.get_response()
        self.assertNotContains(response, "Contributors")
        self.assertNotContains(response, "Rename board")

    def test_template_does_not_contain_delete_when_empty(self):
        self.joe_topic.delete()
        response = self.get_response()
        self.assertNotContains(response, "Delete board")

    def test_not_contributors_board(self):
        "fallback in case template does have the controls"
        data = {"name": "Joe", "description": "Joe board", "contributor": [1]}
        self.post_response(data)
        response = self.get_response()
        board = response.context_data["board"]
        self.assertEqual(board.contributor.count(), 1)

    def test_not_rename_board(self):
        "fallback in case template does have the controls"
        data = {
            "name": "Joe",
            "description": "Joe board",
            "new_board_name": "New name board Joe",
        }
        self.post_response(data)
        response = self.get_response()
        board = response.context_data["board"]
        self.assertEqual(board.name, "Joe")

    def test_not_delete_board(self):
        "fallback in case template does have the controls"
        self.assertEqual(Board.objects.count(), 2)
        self.joe_topic.delete()
        data = {"name": "Joe", "description": "Joe board", "delete_btn": "delete_board"}
        self.post_response(data)
        self.assertEqual(Board.objects.count(), 2)

    def test_template_contains_link_to_user_topic_only(self):
        response = self.get_response()
        topics = response.context_data["topics"]
        self.assertEqual(topics.count(), 1)
        topics_url = reverse(
            "topic_posts",
            kwargs={"board_pk": self.joe_board.pk, "topic_pk": self.joe_topic.pk},
        )
        self.assertContains(response, f'href="{topics_url}"')
