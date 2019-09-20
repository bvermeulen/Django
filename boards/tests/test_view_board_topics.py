from django.contrib.auth.models import User
from django.urls import reverse, resolve
from django.test import TestCase
from ..models import Board
from ..views import TopicListView


class BoardTopicsTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        board = Board.objects.create(name='Django', description='Django board')
        cls.board_pk = board.pk

    def setUp(self):
        self.username = 'joe'
        self.password = '123'
        User.objects.create_user(username=self.username,
                                 email='jane@doe.com', password=self.password)

    def test_board_topics_view_not_found_status_code(self):
        self.client.login(username=self.username, password=self.password)
        url = reverse('board_topics', kwargs={'board_pk': 99})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_board_topics_view_success_status_code(self):
        self.client.login(username=self.username, password=self.password)
        url = reverse('board_topics', kwargs={'board_pk': self.board_pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_board_topics_url_resolves_board_topics_view(self):
        self.client.login(username=self.username, password=self.password)
        view = resolve('/boards/1/topics/')
        self.assertEqual(view.func.view_class, TopicListView)

    def test_board_topics_view_contains_link_back_to_boardpage(self):
        self.client.login(username=self.username, password=self.password)
        board_topics_url = reverse('board_topics', kwargs={'board_pk': self.board_pk})
        boardpage_url = reverse('boards')
        response = self.client.get(board_topics_url)
        self.assertContains(response, f'href="{boardpage_url}"')

    def test_board_topics_view_contains_navigation_links(self):
        self.client.login(username=self.username, password=self.password)
        board_topics_url = reverse('board_topics', kwargs={'board_pk': self.board_pk})
        new_topic_url = reverse('new_topic', kwargs={'board_pk': self.board_pk})
        response = self.client.get(board_topics_url)
        self.assertContains(response, f'href="{new_topic_url}"')
