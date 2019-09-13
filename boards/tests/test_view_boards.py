from django.contrib.auth.models import User
from django.urls import reverse, resolve
from django.test import TestCase
from ..views import BoardListView
from ..models import Board


class BoardsTests(TestCase):
    def setUp(self):
        username = 'joe'
        password = '123'
        _ = User.objects.create_user(username=username,
                                     email='jane@doe.com', password=password)
        self.client.login(username=username, password=password)
        self.board = Board.objects.create(name='Django', description='Django board')
        url = reverse('boards')
        self.response = self.client.get(url)

    def test_boards_view_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_boards_url_resolves_boards_view(self):
        view = resolve('/boards/')
        self.assertEqual(view.func.view_class, BoardListView)

    def test_boards_view_contains_link_to_topics_page(self):
        board_topics_url = reverse('board_topics', kwargs={'board_pk': self.board.pk})
        self.assertContains(self.response, f'href="{board_topics_url}"')
