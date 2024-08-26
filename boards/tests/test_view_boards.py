from django.contrib.auth.models import User
from django.urls import reverse, resolve
from django.test import TestCase
from ..views import BoardListView
from ..models import Board


class BoardsTestsNoLogin(TestCase):
    def setUp(self):
        default_user = User.objects.create_user(
            username="default_user", email="default_user@howdiweb.nl", password="456"
        )
        self.board = Board.objects.create(
            name="Django", description="Django board", owner=default_user
        )
        self.boards_url = reverse("boards")

    def get_response(self):
        return self.client.get(self.boards_url)

    def test_csrf(self):
        self.assertContains(self.get_response(), "csrfmiddlewaretoken")

    def test_boards_url_resolves_boards_view(self):
        view = resolve("/boards/")
        self.assertEqual(view.func.view_class, BoardListView)

    def test_boards_view_status_code(self):
        response = self.get_response()
        self.assertEqual(response.status_code, 200)

    def test_template_contains_link_to_board_topics(self):
        response = self.get_response()
        board_topics_url = reverse("board_topics", kwargs={"board_pk": self.board.pk})
        self.assertContains(response, f'href="{board_topics_url}"')

    def test_template_only_contains_default_board(self):
        response = self.get_response()
        boards = response.context_data["boards"]
        self.assertEqual(len(boards), 1)
        self.assertEqual(boards[0].name, "Django")

    def test_template_does_not_contain_add_board(self):
        response = self.get_response()
        self.assertNotContains(response, "Add board")

    def test_template_does_not_contain_all_boards(self):
        response = self.get_response()
        self.assertNotContains(response, "my boards")


class BoardsTestsUserLogin(TestCase):
    def setUp(self):
        user_joe = User.objects.create_user(
            username="joe", email="joe@doe.com", password="123"
        )
        self.user_jane = User.objects.create_user(
            username="jane", email="jane@doe.com", password="456"
        )
        default_user = User.objects.create_user(
            username="default_user", email="default_user@howdiweb.nl", password="789"
        )
        self.board_default = Board.objects.create(
            name="Django", description="Django board", owner=default_user
        )
        self.board_joe = Board.objects.create(
            name="Joe", description="Joe board", owner=user_joe
        )
        self.board_jane = Board.objects.create(
            name="Jane", description="Jane board", owner=self.user_jane
        )
        self.board_jane.contributor.add(user_joe)
        self.boards_url = reverse("boards")
        self.client.login(username="joe", password="123")

    def get_response(self):
        return self.client.get(self.boards_url)

    def post_response(self, data):
        return self.client.post(self.boards_url, data)

    def test_template_contains_links_to_board_topics(self):
        response = self.get_response()
        board_topics_url = reverse("board_topics", kwargs={"board_pk": self.board_joe.pk})
        self.assertContains(response, f'href="{board_topics_url}"')
        board_topics_url = reverse("board_topics", kwargs={"board_pk": self.board_jane.pk})
        self.assertContains(response, f'href="{board_topics_url}"')
        board_topics_url = reverse("board_topics", kwargs={"board_pk": self.board_default.pk})
        self.assertContains(response, f'href="{board_topics_url}"')

    def test_template_contains_add_board(self):
        response = self.get_response()
        self.assertContains(response, "Add board")

    def test_template_contains_all_boards(self):
        response = self.get_response()
        self.assertContains(response, "my boards")

    def test_template_contains_all_boards(self):
        response = self.get_response()
        boards = response.context_data["boards"]
        self.assertEqual(len(boards), 3)
        self.assertEqual(boards[0].name, "Joe")
        self.assertEqual(boards[1].name, "Jane")
        self.assertEqual(boards[2].name, "Django")

    def test_press_my_boards(self):
        data = {"board_selection": "user_boards"}
        response = self.post_response(data)
        self.assertRedirects(response, self.boards_url)
        response = self.get_response()
        boards = response.context_data["boards"]
        self.assertEqual(len(boards), 1)
        self.assertEqual(boards[0].name, "Joe")
        self.assertContains(response, "all boards")

    def test_add_board(self):
        data = {"board_selection": "user_boards"}
        self.post_response(data)
        data = {"name": "Joe 2nd board", "description": "board added in test"}
        self.post_response(data)
        response = self.get_response()
        boards = response.context_data["boards"]
        self.assertEqual(len(boards), 2)
        self.assertEqual(boards[0].name, "Joe")
        self.assertEqual(boards[1].name, "Joe 2nd board")

    def test_add_board_with_contributor(self):
        data = {"board_selection": "user_boards"}
        self.post_response(data)
        data = {"name": "Joe 2nd board", "description": "contributor should be jane", "contributor": [2]}
        self.post_response(data)
        response = self.get_response()
        boards = response.context_data["boards"]
        self.assertEqual(len(boards), 2)
        self.assertEqual(boards[0].name, "Joe")
        self.assertEqual(boards[1].description, "contributor should be jane")
        self.assertEqual(boards[1].contributor.first().username, "jane")
