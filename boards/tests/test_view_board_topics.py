from django.urls import reverse, resolve
from django.test import TestCase
from ..views import TopicListView
from ..models import Board


class BoardTopicsTests(TestCase):
    def setUp(self):
        Board.objects.create(name='Django', description='Django board')

    def test_board_topics_view_not_found_status_code(self):
        url = reverse('board_topics', kwargs={'board_pk': 99})
        response = self.client.get(url)
        self.assertEquals(response.status_code, 404)

    def test_board_topics_view_success_status_code(self):
        url = reverse('board_topics', kwargs={'board_pk': 1})
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)

    def test_board_topics_url_resolves_board_topics_view(self):
        view = resolve('/boards/1/')
        self.assertEquals(view.func.view_class, TopicListView)

    def test_board_topics_view_contains_link_back_to_boardpage(self):
        board_topics_url = reverse('board_topics', kwargs={'board_pk': 1})
        boardpage_url = reverse('boards')
        new_topic_url = reverse('new_topic', kwargs={'board_pk': 1})

        response = self.client.get(board_topics_url)
        self.assertContains(response, 'href="{0}"'.format(boardpage_url))
        self.assertContains(response, 'href="{0}"'.format(new_topic_url))

    def test_board_topics_view_contains_navigation_links(self):
        board_topics_url = reverse('board_topics', kwargs={'board_pk': 1})
        boardpage_url = reverse('boards')
        new_topic_url = reverse('new_topic', kwargs={'board_pk': 1})

        response = self.client.get(board_topics_url)

        self.assertContains(response, 'href="{0}"'.format(boardpage_url))
        self.assertContains(response, 'href="{0}"'.format(new_topic_url))
