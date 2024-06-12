import itertools
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.views.generic import UpdateView, ListView
from django.db.utils import IntegrityError
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.db.models import Count
from django.core.exceptions import ObjectDoesNotExist
from howdimain.howdimain_vars import POSTS_PER_PAGE, TOPICS_PER_PAGE
from howdimain.utils.plogger import Logger
from howdimain.utils.get_ip import get_client_ip
from .forms import BoardForm, TopicForm, PostForm
from .models import Board, Topic, Post

logger = Logger.getlogger()


class BoardListView(ListView):
    model = Board
    board_form = BoardForm
    context_object_name = "boards"
    template_name = "boards/boards.html"

    def get_context_data(self, **kwargs):
        kwargs["form"] = self.board_form(
            None, initial={"board_selection": self.board_selection}
        )
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        default_user = get_object_or_404(User, username="default_user")
        user = self.request.user
        if user.is_authenticated:
            self.board_selection = self.request.session.get("board_selection", "all_boards")
            boards_user = user.boards.all().order_by("name")
            boards_contributor = Board.objects.filter(contributor=user).order_by("name")
        else:
            boards_user = []
            boards_contributor = []
            self.board_selection = "all_boards"

        boards_default_user = default_user.boards.all().order_by("name")

        match self.board_selection:
            case "all_boards":
                if user == default_user:
                    return list(itertools.chain(
                        boards_default_user, boards_contributor
                    ))
                else:
                    return list(itertools.chain(
                        boards_user, boards_contributor, boards_default_user
                    ))

            case "user_boards":
                return list(itertools.chain(boards_user, boards_contributor))

            case _:
                return boards_default_user

    def post(self, request):
        user = request.user
        form = self.board_form(request.POST)
        request.session["board_selection"] = form.data.get(
            "board_selection", request.session["board_selection"]
        )
        if form.is_valid() and user.is_authenticated:
            board = form.save(commit=False)
            board.owner = user
            try:
                board.save()
                form.save_m2m()
                logger.info(
                    f"{request.user.username} ({get_client_ip(request)}) added a new "
                    f"board: {board.name}"
                )
            except IntegrityError:
                logger.warn(
                    f"{request.user.username} ({get_client_ip(request)}) tried to add a new "
                    f"board: {board.name}, this name already exists"
                )
        return redirect("boards")


@login_required
def my_boards(request):
    request.session["board_selection"] = "user_boards"
    return redirect("boards")


class TopicListView(ListView):
    model = Topic
    board_form = BoardForm
    context_object_name = "topics"
    template_name = "boards/topics.html"
    paginate_by = TOPICS_PER_PAGE

    def get_context_data(self, **kwargs):
        kwargs["board"] = self.board
        kwargs["form"] = self.board_form(
            None,
            initial={
                "name": self.board.name,
                "description": self.board.description,
                "contributor": [i.id for i in self.board.contributor.all()],
            },
        )
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        self.board = get_object_or_404(Board, pk=self.kwargs.get("board_pk"))
        topics = self.board.topics.order_by(
            "-last_updated",
        ).annotate(contributions=Count("posts"))
        return topics

    def post(self, request, board_pk):
        user = request.user
        board = get_object_or_404(Board, pk=board_pk)
        form = self.board_form(request.POST)
        if user.is_authenticated and form.is_valid():
            delete_btn = form.cleaned_data.get("delete_btn", "")
            new_board_name = form.cleaned_data.get("new_board_name", "")
            contributors = form.cleaned_data.get("contributor", [])
            if (
                delete_btn == "delete_board"
                and not board.topics.all()
                and user == board.owner
            ):
                logger.info(
                    f"{user.username} ({get_client_ip(request)}) "
                    f"deleted board: {board.name}"
                )
                board.delete()
                return redirect("boards")

            old_board_name = board.name
            if new_board_name and user == board.owner:
                board.name = new_board_name[0:30]
                logger.info(
                    f"{user.username} ({get_client_ip(request)}) "
                    f"renamed board: {old_board_name} to {board.name}"
                )

            if user == board.owner:
                if set(board.contributor.all().all()) != set(contributors):
                    board.contributor.clear()
                    board.contributor.set(contributors)
                    logger.info(
                        f"{user.username} ({get_client_ip(request)}) "
                        f"changed contributors for board: {board.name}"
                    )
                board.save()

        return redirect("board_topics", board_pk=board_pk)


@login_required
def new_topic(request, board_pk):
    board = get_object_or_404(Board, pk=board_pk)

    if request.method == "POST":
        form1 = TopicForm(request.POST)
        form2 = PostForm(request.POST)
        if form1.is_valid() and form2.is_valid():
            topic = form1.save(commit=False)
            topic.board = board
            topic.starter = request.user
            topic.last_updated = timezone.now()
            topic.save()

            post = form2.save(commit=False)
            post.topic = topic
            post.created_by = topic.starter
            post.created_at = topic.last_updated
            # first post for topic then updated is same as created
            post.updated_by = post.created_by
            post.updated_at = post.created_at
            post.save()
            # save the m2m field 'allowed user'
            form2.save_m2m()
            logger.info(
                f"{request.user.username} ({get_client_ip(request)}) created new "
                f"topic: {topic.topic_subject} with post: {post.post_subject}"
            )
            return redirect("topic_posts", board_pk=board.pk, topic_pk=topic.pk)

    else:
        form1 = TopicForm()
        form2 = PostForm()

    context = {
        "board": board,
        "form1": form1,
        "form2": form2,
    }
    return render(request, "boards/new_topic.html", context)


class PostListView(ListView):
    model = Post
    context_object_name = "posts"
    template_name = "boards/topic_posts.html"
    paginate_by = POSTS_PER_PAGE

    def get_context_data(self, **kwargs):
        session_key = f"viewed_topic_{self.topic.pk}"
        if not self.request.session.get(session_key, False):
            self.topic.views += 1
            self.topic.save()
            self.request.session[session_key] = True

        try:
            moderator = User.objects.get(username="moderator")
        except ObjectDoesNotExist:
            moderator = ""
        kwargs["topic"] = self.topic
        kwargs["moderator"] = moderator
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        self.topic = get_object_or_404(
            Topic, board__pk=self.kwargs.get("board_pk"), pk=self.kwargs.get("topic_pk")
        )

        queryset = self.topic.posts.order_by("-updated_at")
        return queryset

    # handle deletion of a post
    def post(self, request, **kwargs):
        deleted_post_pk = int(self.request.POST.get("deleted_post_pk"))
        original_post_pks = [post.pk for post in self.get_queryset()]
        deleted_index_pk = original_post_pks.index(deleted_post_pk)
        new_index_pk = 1 if deleted_index_pk == 0 else deleted_index_pk - 1
        new_post_pk = (
            None if len(original_post_pks) == 1 else original_post_pks[new_index_pk]
        )
        post_candidate_delete = get_object_or_404(Post, pk=deleted_post_pk)
        logger.info(
            f"{request.user.username} ({get_client_ip(request)}) deleted "
            f"post: {post_candidate_delete.post_subject}"
        )
        post_candidate_delete.delete()
        self.topic.last_updated = timezone.now()
        self.topic.save()

        if new_post_pk:
            topic_url = reverse(
                "topic_posts",
                kwargs={
                    "board_pk": self.topic.board.pk,
                    "topic_pk": self.topic.pk,
                },
            )
            topic_post_url = (
                f"{topic_url}?page={self.topic.get_page_number(new_post_pk)}"
            )
            return redirect(topic_post_url)
        else:
            # if no posts left for the topic then also delete the topic
            get_object_or_404(Topic, pk=self.topic.pk).delete()
            topics_url = reverse(
                "board_topics", kwargs={"board_pk": self.topic.board.pk}
            )
            return redirect(topics_url)


@login_required
def add_post_to_topic(request, board_pk, topic_pk):
    topic = get_object_or_404(Topic, board__pk=board_pk, pk=topic_pk)
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.topic = topic
            post.created_by = request.user
            post.created_at = timezone.now()
            post.updated_by = post.created_by
            post.updated_at = post.created_at
            post.save()
            form.save_m2m()
            topic.last_updated = timezone.now()
            topic.save()

            topic_url = reverse(
                "topic_posts", kwargs={"board_pk": board_pk, "topic_pk": topic_pk}
            )
            topic_post_url = f"{topic_url}?page={topic.get_page_number(post.pk)}"
            logger.info(
                f"{request.user.username} ({get_client_ip(request)}) added a new "
                f"post: {post.post_subject}"
            )
            return redirect(topic_post_url)
    else:
        form = PostForm()

    context = {"topic": topic, "form": form}
    return render(request, "boards/add_to_topic.html", context)


@method_decorator(login_required, name="dispatch")
class PostUpdateView(UpdateView):
    model = Post
    form_class = PostForm
    template_name = "boards/edit_post.html"
    pk_url_kwarg = "post_pk"
    context_object_name = "post"

    def get_queryset(self):
        self.topic = get_object_or_404(
            Topic, board__pk=self.kwargs.get("board_pk"), pk=self.kwargs.get("topic_pk")
        )
        queryset = self.topic.posts.order_by("-updated_at")

        _post = get_object_or_404(Post, pk=self.kwargs.get("post_pk"))
        try:
            moderator = User.objects.get(username="moderator")

        except ObjectDoesNotExist:
            moderator = ""

        self.allowed_to_edit = (
            self.request.user == _post.created_by
            or self.request.user == moderator
            or self.request.user in _post.allowed_editor.all()
        )

        return queryset

    # handle deletion of a post
    def delete_post(self):
        try:
            deleted_post_pk = int(self.request.POST.get("deleted_post_pk"))
        except TypeError:
            return False

        # obtain the new_post_pk; if the last post is deleted new_post_pk is None
        original_post_pks = [post.pk for post in self.get_queryset()]
        deleted_index_pk = original_post_pks.index(deleted_post_pk)
        new_index_pk = 1 if deleted_index_pk == 0 else deleted_index_pk - 1
        self.new_post_pk = (
            None if len(original_post_pks) == 1 else original_post_pks[new_index_pk]
        )

        post_candidate_delete = get_object_or_404(Post, pk=deleted_post_pk)
        logger.info(
            f"{self.request.user.username} ({get_client_ip(self.request)}) deleted "
            f"post: {post_candidate_delete.post_subject}"
        )
        post_candidate_delete.delete()
        return True

    def form_valid(self, form):

        # check against manual editing of html input in browser if  user is
        # allowed to edit this post
        if not self.allowed_to_edit:
            topic_url = reverse(
                "topic_posts",
                kwargs={"board_pk": self.topic.board.pk, "topic_pk": self.topic.pk},
            )
            topic_post_url = (
                f"{topic_url}?page="
                f'{self.topic.get_page_number(self.kwargs.get("post_pk"))}'
            )
            return redirect(topic_post_url)

        self.topic.last_updated = timezone.now()
        self.topic.save()

        if self.delete_post():
            if self.new_post_pk:
                # redirect to the topic post page
                topic_url = reverse(
                    "topic_posts",
                    kwargs={
                        "board_pk": self.topic.board.pk,
                        "topic_pk": self.topic.pk,
                    },
                )
                url_after_delete = (
                    f"{topic_url}?page="
                    f"{self.topic.get_page_number(self.new_post_pk)}"
                )
            else:
                # if no posts left for the topic then also delete the topic
                # and redirect to the boards page
                get_object_or_404(Topic, pk=self.topic.pk).delete()
                url_after_delete = reverse(
                    "board_topics", kwargs={"board_pk": self.topic.board.pk}
                )

            return redirect(url_after_delete)

        else:
            # note if commit=False, then post.save() must be followed by form.save_m2m()
            post = form.save(commit=False)
            post.updated_by = self.request.user
            post.updated_at = self.topic.last_updated
            post.save()
            form.save_m2m()
            logger.info(
                f"{self.request.user.username} ({get_client_ip(self.request)}) updated "
                f"post {post.post_subject}"
            )
            topic_url = reverse(
                "topic_posts",
                kwargs={"board_pk": self.topic.board.pk, "topic_pk": self.topic.pk},
            )
            topic_post_url = f"{topic_url}?page={self.topic.get_page_number(post.pk)}"

            return redirect(topic_post_url)
