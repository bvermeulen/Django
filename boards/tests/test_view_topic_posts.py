from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve, reverse
from ..models import Board, Post, Topic
from ..views import PostListView


class TopicPostsTests(TestCase):
    def setUp(self):
        username = 'john'
        email = 'john@doe.com'
        password = '123'
        user = User.objects.create_user(username=username,
                                        email=email, password=password)
        self.client.login(username=username, password=password)

        board = Board.objects.create(name='Django', description='Django board')
        topic = Topic.objects.create(topic_subject='Hello, world',
                                     board=board, starter=user)
        Post.objects.create(post_subject='Quod io', message='Lorem ipsum dolor sit amet',
                            topic=topic, created_by=user)
        context = {'board_pk': board.pk, 'topic_pk': topic.pk}
        url = reverse('topic_posts', kwargs=context)
        self.response = self.client.get(url)

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_view_function(self):
        view = resolve('/boards/1/topics/1/posts/')
        self.assertEqual(view.func.view_class, PostListView)
