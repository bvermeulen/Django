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
        self.owner = 'owner'
        self.owner_pw = 'owner_123'
        user = User.objects.create_user(username=self.owner,
                                        email='owner@doe.com', password=self.owner_pw)

        user_joe = User.objects.create_user(username='joe',
                                            email='joe@joe.com',
                                            password='joe_123')

        User.objects.create_user(username='moderator',
                                 email='moderator@howdiweb.com',
                                 password='moderator_123')

        User.objects.create_user(username='jane',
                                 email='jane@google.com',
                                 password='jane_123')

        self.topic = Topic.objects.create(topic_subject='Hello, world',
                                          board=self.board, starter=user)
        self.post = Post.objects.create(post_subject='Quod',
                                        message='Lorem ipsum dolor sit amet',
                                        topic=self.topic,
                                        created_by=user,)

        self.post.allowed_editor.add(user_joe)

        self.url = reverse('edit_post', kwargs={'board_pk': self.board.pk,
                                                'topic_pk': self.topic.pk,
                                                'post_pk': self.post.pk
                                               })


class LoginRequiredPostUpdateViewTests(PostUpdateViewTestCase):

    def test_redirection(self):
        login_url = reverse('login')
        response = self.client.get(self.url)
        self.assertRedirects(response, f'{login_url}?next={self.url}')


class PostUpdateViewTests(PostUpdateViewTestCase):

    def setUp(self):
        super().setUp()
        self.client.login(username=self.owner, password=self.owner_pw)
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
            6 <input: csrf, owner, Joe (allowed to edit), Jane
                      post_subject, markdown_image_upload
            1 <textarea: message
        '''
        self.assertContains(self.response, '<input', 6)
        self.assertContains(self.response, '<textarea', 1)


class UnauthorizedPostUpdateViewTests(PostUpdateViewTestCase):

    def test_status_code(self):
        '''
        A topic should be edited only by the owner and allow editors
        Unauthorized users should get a 302 response (redirect)
        as nothing is changed
        '''
        self.client.login(username='jane', password='jane_123')
        data = {'post_subject': 'jane',
                'message': 'jane edited'}

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)


class SuccessfulPostUpdateViewTests(PostUpdateViewTestCase):

    def test_redirection(self):
        '''
        A valid form submission should redirect the user
        '''
        self.client.login(username=self.owner, password=self.owner_pw)
        data = {'post_subject': 'my edit',
                'message': 'edited message',
               }
        response = self.client.post(self.url, data)

        topic_posts_url = reverse('topic_posts', kwargs={'board_pk': self.board.pk,
                                                         'topic_pk': self.topic.pk})
        topic_posts_url += '?page=1'

        self.assertRedirects(response, topic_posts_url)

    def test_post_changed(self):
        self.client.login(username=self.owner, password=self.owner_pw)
        data = {'post_subject': 'my edit',
                'message': 'edited message',
               }
        self.client.post(self.url, data)

        self.post.refresh_from_db()
        self.assertEqual(self.post.message, 'edited message')

    def test_post_changed_by_moderator_redirection(self):
        self.client.login(username='moderator', password='moderator_123')
        data = {'post_subject': 'moderator edit',
                'message': 'moderator has edited'}

        response = self.client.post(self.url, data)
        topic_posts_url = reverse('topic_posts', kwargs={'board_pk': self.board.pk,
                                                         'topic_pk': self.topic.pk})
        topic_posts_url += '?page=1'
        self.assertRedirects(response, topic_posts_url)

    def test_post_changed_by_moderator(self):
        self.client.login(username='moderator', password='moderator_123')
        data = {'post_subject': 'moderator edit',
                'message': 'moderator has edited'}

        self.client.post(self.url, data)
        self.post.refresh_from_db()
        self.assertEqual(self.post.message, 'moderator has edited')

    def test_post_changed_by_allowed_editor_redirection(self):
        self.client.login(username='joe', password='joe_123')
        data = {'post_subject': 'joe edit',
                'message': 'joe has edited'}

        response = self.client.post(self.url, data)
        topic_posts_url = reverse('topic_posts', kwargs={'board_pk': self.board.pk,
                                                         'topic_pk': self.topic.pk})
        topic_posts_url += '?page=1'
        self.assertRedirects(response, topic_posts_url)

    def test_post_changed_by_allowed_editor(self):
        self.client.login(username='joe', password='joe_123')
        data = {'post_subject': 'joe edit',
                'message': 'joe has edited'}

        self.client.post(self.url, data)
        self.post.refresh_from_db()
        self.assertEqual(self.post.message, 'joe has edited')


class InvalidPostUpdateViewTests(PostUpdateViewTestCase):
    def setUp(self):
        super().setUp()
        self.client.login(username=self.owner, password=self.owner_pw)

    def test_status_code(self):
        '''
        Submit an empty dictionary to the `add_to_topic` view
        An invalid form submission should return to the same page
        '''
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 200)

    def test_form_errors(self):
        response = self.client.post(self.url, {})
        form = response.context.get('form')
        self.assertTrue(form.errors)

    def test_not_any_user_can_edit(self):
        self.client.logout()
        self.client.login(username='jane', password='jane_123')
        data = {'post_subject': 'jane edit',
                'message': 'jane has edited'}
        self.client.post(self.url, data)

        self.post.refresh_from_db()
        self.assertEqual(self.post.message, 'Lorem ipsum dolor sit amet')
