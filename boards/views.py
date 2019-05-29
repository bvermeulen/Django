from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.views.generic import UpdateView, ListView
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.db.models import Count
from .forms import NewTopicForm, PostForm
from .models import Board, Topic, Post, AllowedUser
from .boards_settings import POSTS_PER_PAGE, TOPICS_PER_PAGE

@method_decorator(login_required, name='dispatch')
class BoardListView(ListView):
    model = Board
    context_object_name = 'boards'
    template_name = 'boards/boards.html'


@method_decorator(login_required, name='dispatch')
class TopicListView(ListView):
    model = Topic
    context_object_name = 'topics'
    template_name = 'boards/topics.html'
    paginate_by = TOPICS_PER_PAGE

    def get_context_data(self, **kwargs):
        kwargs['board'] = self.board
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        self.board = get_object_or_404(Board, pk=self.kwargs.get('board_pk'))
        queryset = self.board.topics.order_by('-last_updated', )\
                                    .annotate(contributions=Count('posts'))
        return queryset


@login_required
def new_topic(request, board_pk):
    board = get_object_or_404(Board, pk=board_pk)

    if request.method == 'POST':
        form1 = NewTopicForm(request.POST)
        form2 = PostForm(request.POST)
        if form1.is_valid() and form2.is_valid():
            topic = form1.save(commit=False)
            post = form2.save(commit=False)
            topic.board = board
            topic.starter = request.user
            topic.last_updated = timezone.now()
            topic.save()

            post.topic = topic
            post.created_by = topic.starter
            post.created_at = topic.last_updated
            # first post for topic then updated is same as created
            post.updated_by= post.created_by
            post.updated_at= post.created_at
            post.save()
            # save the m2m field 'allowed user'
            form2.save_m2m()

            return redirect('topic_posts', board_pk=board.pk, topic_pk=topic.pk)

    else:
        form1 = NewTopicForm()
        form2 = PostForm()

    context = { 'board': board,
                'form1': form1,
                'form2': form2, }
    return render(request, 'boards/new_topic.html', context)


@method_decorator(login_required, name='dispatch')
class PostListView(ListView):
    model = Post
    context_object_name = 'posts'
    template_name = 'boards/topic_posts.html'
    paginate_by = POSTS_PER_PAGE

    def get_context_data(self, **kwargs):
        session_key = f'viewed_topic_{self.topic.pk}'
        if not self.request.session.get(session_key, False):
            self.topic.views += 1
            self.topic.save()
            self.request.session[session_key] = True
        kwargs['topic'] = self.topic

        return super().get_context_data(**kwargs)

    def get_queryset(self):
        self.topic = get_object_or_404(Topic,
                                       board__pk=self.kwargs.get('board_pk'),
                                       pk=self.kwargs.get('topic_pk'))

        queryset = self.topic.posts.order_by('-updated_at')

        return queryset

    # handle deletion of a post
    def post(self, *args, **kwargs):
        deleted_post_pk = int(self.request.POST.get('deleted_post_pk'))
        original_post_pks = [post.pk for post in self.get_queryset()]
        deleted_index_pk = original_post_pks.index(deleted_post_pk)
        if deleted_index_pk == 0:
            # note index 0 will be deleted so index 1 will become index 0
            new_index_pk = 1
        else:
            new_index_pk = deleted_index_pk - 1

        if len(original_post_pks) == 1:
            new_post_pk = None
            # new_index_pk = None
        else:
            new_post_pk = original_post_pks[new_index_pk]

        get_object_or_404(Post, pk=deleted_post_pk).delete()

        self.topic.last_updated = timezone.now()
        self.topic.save()

        if new_post_pk:
            topic_url = reverse('topic_posts',
                                kwargs={'board_pk': self.topic.board.pk,
                                        'topic_pk': self.topic.pk,})
            topic_post_url = f'{topic_url}?page={self.topic.get_page_number(new_post_pk)}'
            return redirect(topic_post_url)
        else:
            # if no posts left for the topic then also delete the topic
            get_object_or_404(Topic, pk=self.topic.pk).delete()
            topics_url = reverse('board_topics', kwargs={'board_pk': self.topic.board.pk})
            return redirect(topics_url)


@login_required
def add_to_topic(request, board_pk, topic_pk):
    topic = get_object_or_404(Topic, board__pk=board_pk, pk=topic_pk)
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.topic = topic
            post.created_by = request.user
            post.created_at = timezone.now()
            # if new post is added then make updated same as created
            post.updated_by = post.created_by
            post.updated_at = post.created_at

            post.save()
            form.save_m2m()

            topic.last_updated = timezone.now()
            topic.save()

            topic_url = reverse('topic_posts',
                                kwargs={'board_pk': board_pk,
                                        'topic_pk': topic_pk})
            topic_post_url = f'{topic_url}?page={topic.get_page_number(post.pk)}'
            return redirect(topic_post_url)
    else:
        form = PostForm()

    context = {'topic': topic, 'form': form}
    return render(request, 'boards/add_to_topic.html', context)


@method_decorator(login_required, name='dispatch')
class PostUpdateView(UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'boards/edit_post.html'
    pk_url_kwarg = 'post_pk'
    context_object_name = 'post'

    def get_queryset(self):
        self.topic = get_object_or_404(Topic,
                                       board__pk=self.kwargs.get('board_pk'),
                                       pk=self.kwargs.get('topic_pk'))
        queryset = self.topic.posts.order_by('-updated_at')

        _post = get_object_or_404(Post, pk=self.kwargs.get('post_pk'))
        self.allowed_to_edit = self.request.user == _post.created_by or \
                               self.request.user in _post.allowed_editor.all()

        return queryset

    # handle deletion of a post
    def delete_post(self):
        try:
            deleted_post_pk = int(self.request.POST.get('deleted_post_pk'))
        except TypeError:
            return False

        original_post_pks = [post.pk for post in self.get_queryset()]
        deleted_index_pk = original_post_pks.index(deleted_post_pk)

        if deleted_index_pk == 0:
            # note index 0 will be deleted so index 1 will become index 0
            new_index_pk = 1
        else:
            new_index_pk = deleted_index_pk - 1

        if len(original_post_pks) == 1:
            self.new_post_pk = None
            # new_index_pk = None
        else:
            self.new_post_pk = original_post_pks[new_index_pk]

        get_object_or_404(Post, pk=deleted_post_pk).delete()
        return True

    def form_valid(self, form):
        # check against manual editing of html input in browser if  user is
        # allowed to edit this post
        if not self.allowed_to_edit:
            topic_url = reverse('topic_posts',
                                kwargs={'board_pk': self.topic.board.pk,
                                        'topic_pk': self.topic.pk},)
            topic_post_url = f'{topic_url}?page={self.topic.get_page_number(self.kwargs.get("post_pk"))}'
            return redirect(topic_post_url)

        self.topic.last_updated = timezone.now()
        self.topic.save()

        if self.delete_post():
            if self.new_post_pk:
                # redirect to the topic post page
                topic_url = reverse('topic_posts',
                                    kwargs={'board_pk': self.topic.board.pk,
                                            'topic_pk': self.topic.pk,})
                url_after_delete = f'{topic_url}?page={self.topic.get_page_number(self.new_post_pk)}'
            else:
                # if no posts left for the topic then also delete the topic
                # and redirect to the boards page
                get_object_or_404(Topic, pk=self.topic.pk).delete()
                url_after_delete = reverse('board_topics', kwargs={'board_pk': self.topic.board.pk})

            return redirect(url_after_delete)

        else:
            # note if commit=False, then post.save() must be followed by form.save_m2m()
            post = form.save(commit=False)
            post.updated_by = self.request.user
            post.updated_at = self.topic.last_updated
            post.save()
            form.save_m2m()

            topic_url = reverse('topic_posts',
                                kwargs={'board_pk': self.topic.board.pk,
                                        'topic_pk': self.topic.pk},)
            topic_post_url = f'{topic_url}?page={self.topic.get_page_number(post.pk)}'
            return redirect(topic_post_url)
