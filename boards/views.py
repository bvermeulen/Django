from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.views.generic import UpdateView, ListView
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.db.models import Count
from .forms import NewTopicForm, PostForm
from .models import Home, Board, Topic, Post


class HomeListView(ListView):
    model = Home
    context_object_name = 'home'
    template_name = 'home.html'


class BoardListView(ListView):
    model = Board
    context_object_name = 'boards'
    template_name = 'boards.html'


class TopicListView(ListView):
    model = Topic
    context_object_name = 'topics'
    template_name = 'topics.html'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        kwargs['board'] = self.board
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        self.board = get_object_or_404(Board, pk=self.kwargs.get('board_pk'))
        queryset = self.board.topics.order_by('-last_updated', ).\
                                     annotate(replies=Count('posts')-1)
        return queryset


@login_required
def new_topic(request, board_pk):
    board = get_object_or_404(Board, pk=board_pk)

    if request.method == 'POST':
        form = NewTopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.board = board
            topic.starter = request.user
            topic.save()
            Post.objects.create(
                message=form.cleaned_data.get('message'),
                topic=topic,
                created_by=request.user)
            return redirect('topic_posts', board_pk=board.pk, topic_pk=topic.pk)

    else:
        form = NewTopicForm()

    return render(request, 'new_topic.html', {'board': board, 'form': form})


class PostListView(ListView):
    model = Post
    context_object_name = 'posts'
    template_name = 'topic_posts.html'
    paginate_by = 2

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
        queryset = self.topic.posts.order_by('created_at')
        return queryset

    def post(self, request, *args, **kwargs):
        deleted_post_pk = int(request.POST.get('deleted_post_pk'))
        nl = '\n'
        print(f'deleted_post_pk: {deleted_post_pk}{nl}')

        original_post_pks = [post.pk for post in self.get_queryset()]
        deleted_index_pk = original_post_pks.index(deleted_post_pk)
        new_index_pk = max(0, deleted_index_pk - 1)
        print(f'original_post_pks: {original_post_pks}{nl}'\
              f'deleted_index_pk: {deleted_index_pk}{nl}'\
              f'deleted_post_pk: {get_object_or_404(Post, pk=deleted_post_pk).pk}{nl}'\
              f'deleted message: {get_object_or_404(Post, pk=deleted_post_pk).message}')

        get_object_or_404(Post, pk=deleted_post_pk).delete()
        try:
            new_post_pks = [post.pk for post in self.get_queryset()]
            new_post_pk = new_post_pks[new_index_pk]
            print(f'new_post_pks: {new_post_pks}{nl}'\
                  f'new_index_pk: {new_index_pk}{nl}')
            print(f'new_post_pk: {get_object_or_404(Post, pk=new_post_pk).pk}{nl}'\
                  f'new message: {get_object_or_404(Post, pk=new_post_pk).message}')
        except:
            print('no more posts!')
            new_post_pk = None

        topic_url = reverse('topic_posts',
                            kwargs={'board_pk': self.topic.board.pk,
                                    'topic_pk': self.topic.pk,})
        topic_post_url = f'{topic_url}?page={self.topic.get_page_number(new_post_pk)}'
        return redirect(topic_post_url)

@login_required
def reply_topic(request, board_pk, topic_pk):
    topic = get_object_or_404(Topic, board__pk=board_pk, pk=topic_pk)
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.topic = topic
            post.created_by = request.user
            post.save()

            topic.last_updated = timezone.now()
            topic.save()

            topic_url = reverse('topic_posts',
                                kwargs={'board_pk': board_pk,
                                        'topic_pk': topic_pk})
            topic_post_url = f'{topic_url}?page={topic.get_page_count()}'
            return redirect(topic_post_url)
    else:
        form = PostForm()

    context = {'topic': topic, 'form': form}
    return render(request, 'reply_topic.html', context)


@method_decorator(login_required, name='dispatch')
class PostUpdateView(UpdateView):
    model = Post
    fields = ('message', )
    template_name = 'edit_post.html'
    pk_url_kwarg = 'post_pk'
    context_object_name = 'post'

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(created_by=self.request.user)

    def form_valid(self, form):
        post = form.save(commit=False)
        post.updated_by = self.request.user
        post.updated_at = timezone.now()
        post.save()

        topic_url = reverse('topic_posts',
                            kwargs={'board_pk': post.topic.board.pk,
                                    'topic_pk': post.topic.pk},)
        topic_post_url = f'{topic_url}?page={post.topic.get_page_number(post.pk)}'
        return redirect(topic_post_url)
