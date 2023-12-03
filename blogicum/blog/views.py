from datetime import datetime

from django.http import Http404
from django.db.models import Q, Count
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView, DetailView
)

from .models import Post, Category, User, Comment
from .forms import PostForm, UserForm, CommentForm

VISIBLE_POSTS = 10


class PostMixin:
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'


class PostListView(PostMixin, ListView):
    template_name = 'blog/index.html'
    ordering = '-pub_date'
    paginate_by = VISIBLE_POSTS
    queryset = Post.objects.annotate(
            comment_count=Count('comments')
        ).select_related(
            'category', 'location', 'author'
        ).filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=datetime.now()
        )


class PostCreateView(LoginRequiredMixin, PostMixin, CreateView):

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(PostMixin, LoginRequiredMixin, UpdateView):

    def dispatch(self, request, *args, **kwargs):
        self._post = get_object_or_404(
            Post,
            pk=kwargs['post_id']
        )
        if request.user != self._post.author:
            return redirect(
                'blog:post_detail',
                post_id=self.kwargs['post_id']
            )
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self._post.pk}
        )


class PostDeleteView(LoginRequiredMixin, PostMixin, DeleteView):
    success_url = reverse_lazy('blog:index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm(instance=self.get_object())
        return context

    def dispatch(self, request, *args, **kwargs):
        if request.user != self.get_object().author:
            raise Http404
        return super().dispatch(request, *args, **kwargs)


class PostDetailView(PostMixin, DetailView):
    template_name = 'blog/detail.html'

    def dispatch(self, request, *args, **kwargs):
        if (request.user != self.get_object(
        ).author) and (not self.get_object().is_published):
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related(
            'author'
        )
        return context


class CategoryListView(ListView):
    model = Post
    template_name = 'blog/category.html'
    paginate_by = VISIBLE_POSTS

    def get_queryset(self):
        queryset = Post.objects.annotate(
            comment_count=Count('comments')
            ).select_related(
                'category'
            ).filter(
            category__slug=self.kwargs['category_slug'],
            category__is_published=True,
            is_published=True,
            pub_date__lte=datetime.now()
        ).order_by('-pub_date')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True,
        )
        return context


class ProfileUser(ListView):
    model = Post
    paginate_by = VISIBLE_POSTS
    template_name = 'blog/profile.html'

    def get_queryset(self):
        queryset = Post.objects.annotate(
            comment_count=Count('comments')
        ).select_related('author').filter(
            Q(author__username=self.kwargs['username'])
            & Q(is_published=True)
            & Q(pub_date__lte=datetime.utcnow())
            | (Q(is_published=False)
                & Q(author__username=self.request.user.username)
                | Q(pub_date__gte=datetime.utcnow()))
        ).order_by('-pub_date')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(
            User,
            username=self.kwargs['username']
        )
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = 'blog/user.html'

    def get_object(self):
        user = self.request.user
        return user

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class CommentCreateView(LoginRequiredMixin, CreateView):
    _post = None
    model = Comment
    form_class = CommentForm
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        self._post = (
            get_object_or_404(
                Post,
                pk=kwargs['post_id'],
            )
        )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self._post
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self._post.pk})


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def get_object(self):
        instance = get_object_or_404(
            Comment,
            pk=self.kwargs['comment_id'],
            author=self.request.user
        )
        return instance

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']}
        )


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'

    def get_object(self):
        instance = get_object_or_404(
            Comment,
            pk=self.kwargs['comment_id'],
            author=self.request.user
        )
        return instance

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']}
        )
