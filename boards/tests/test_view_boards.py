from django.urls import reverse, resolve
from django.test import TestCase
from ..views import BoardListView
from ..models import Board


class BoardsTests(TestCase):
    def setUp(self):
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
        self.assertContains(self.response, 'href="{0}"'.format(board_topics_url))
