import time
from django.contrib.auth.models import User
from django.urls import reverse, resolve
from django.test import TestCase
from ..models import Board
from ..views import TopicListView


class BoardTopicsTests(TestCase):
    def setUp(self):
        username = 'joe'
        password = '123'
        User.objects.create_user(username=username,
                                 email='jane@doe.com', password=password)
        self.client.login(username=username, password=password)
        Board.objects.create(name='Django', description='Django board')

    def test_board_topics_view_not_found_status_code(self):
        url = reverse('board_topics', kwargs={'board_pk': 99})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_board_topics_view_success_status_code(self):
        url = reverse('board_topics', kwargs={'board_pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_board_topics_url_resolves_board_topics_view(self):
        view = resolve('/boards/1/topics/')
        self.assertEqual(view.func.view_class, TopicListView)

    def test_board_topics_view_contains_link_back_to_boardpage(self):
        board_topics_url = reverse('board_topics', kwargs={'board_pk': 1})
        boardpage_url = reverse('boards')
        response = self.client.get(board_topics_url)
        self.assertContains(response, f'href="{boardpage_url}"')

    def test_board_topics_view_contains_navigation_links(self):
        board_topics_url = reverse('board_topics', kwargs={'board_pk': 1})
        new_topic_url = reverse('new_topic', kwargs={'board_pk': 1})
        response = self.client.get(board_topics_url)
        time.sleep(0.5)
        self.assertContains(response, f'href="{new_topic_url}"')
