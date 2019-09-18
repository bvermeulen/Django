from django.forms import ModelForm
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve, reverse
from ..models import Board, Post, Topic
from ..views import PostUpdateView

class PostUpdateViewTestCase(TestCase):
    '''
    Base test case to be used in all `PostUpdateView` view tests
    '''
    def setUp(self):
        self.board = Board.objects.create(name='Django', description='Django board.')
        self.username = 'john'
        self.password = '123'
        user = User.objects.create_user(username=self.username,
                                        email='john@doe.com', password=self.password)
        self.topic = Topic.objects.create(topic_subject='Hello, world',
                                          board=self.board, starter=user)
        self.post = Post.objects.create(post_subject='Quod',
                                        message='Lorem ipsum dolor sit amet',
                                        topic=self.topic, created_by=user)
        self.url = reverse('edit_post', kwargs={'board_pk': self.board.pk,
                                                'topic_pk': self.topic.pk,
                                                'post_pk': self.post.pk
                                               })


class LoginRequiredPostUpdateViewTests(PostUpdateViewTestCase):
    def test_redirection(self):
        login_url = reverse('login')
        response = self.client.get(self.url)
        self.assertRedirects(response, f'{login_url}?next={self.url}')

class UnauthorizedPostUpdateViewTests(PostUpdateViewTestCase):
    def setUp(self):
        super().setUp()
        username = 'jane'
        password = '321'
        _ = User.objects.create_user(username=username,
                                     email='jane@doe.com', password=password)
        self.client.login(username=username, password=password)
        data = {'post_subject': 'jane',
                'message': '321'}
        self.response = self.client.post(self.url, data)

    def test_status_code(self):
        '''
        A topic should be edited only by the owner.
        Unauthorized users should get a 302 response (redirect)
        as nothing is changed
        '''
        self.assertEqual(self.response.status_code, 302)


class PostUpdateViewTests(PostUpdateViewTestCase):
    def setUp(self):
        super().setUp()
        self.client.login(username=self.username, password=self.password)
        self.response = self.client.get(self.url)

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_view_class(self):
        view = resolve('/boards/1/topics/1/posts/1/edit/')
        self.assertEqual(view.func.view_class, PostUpdateView)

    def test_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_contains_form(self):
        form = self.response.context.get('form')
        self.assertIsInstance(form, ModelForm)

    def test_form_inputs(self):
        '''
        The view must contain:
            4 <inpu: csrf, allowed_editor, post_subject, markdown_image_upload
            1 <textarea: message
        '''
        self.assertContains(self.response, '<input', 4)
        self.assertContains(self.response, '<textarea', 1)


class SuccessfulPostUpdateViewTests(PostUpdateViewTestCase):
    def setUp(self):
        super().setUp()
        self.client.login(username=self.username, password=self.password)
        data = {'post_subject': 'my edit',
                'message': 'edited message'}
        self.response = self.client.post(self.url, data)

    def test_redirection(self):
        '''
        A valid form submission should redirect the user
        '''
        topic_posts_url = reverse('topic_posts', kwargs={'board_pk': self.board.pk,
                                                         'topic_pk': self.topic.pk})
        topic_posts_url += '?page=1'
        self.assertRedirects(self.response, topic_posts_url)

    def test_post_changed(self):
        self.post.refresh_from_db()
        self.assertEqual(self.post.message, 'edited message')


class InvalidPostUpdateViewTests(PostUpdateViewTestCase):
    def setUp(self):
        '''
        Submit an empty dictionary to the `add_to_topic` view
        '''
        super().setUp()
        self.client.login(username=self.username, password=self.password)
        self.response = self.client.post(self.url, {})

    def test_status_code(self):
        '''
        An invalid form submission should return to the same page
        '''
        self.assertEqual(self.response.status_code, 200)

    def test_form_errors(self):
        form = self.response.context.get('form')
        self.assertTrue(form.errors)
