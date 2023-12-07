from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)

from blog.forms import CommentForm, UserForm
from blog.mixins import CommentMixin, PostAddition, PostDispMixin, PostMixin
from blog.models import Category, Comment, Post, User


class PostListView(PostAddition, PostMixin, ListView):
    template_name = 'blog/index.html'


class PostCreateView(LoginRequiredMixin, PostMixin, CreateView):

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, PostMixin, PostDispMixin, UpdateView):

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.get_object().pk}
        )


class PostDeleteView(LoginRequiredMixin, PostMixin, PostDispMixin, DeleteView):
    success_url = reverse_lazy('blog:index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm(instance=self.get_object())
        return context


class PostDetailView(PostMixin, DetailView):
    template_name = 'blog/detail.html'

    def get_object(self):
        obj = super().get_object()
        if (self.request.user != obj.author) and (
            (not obj.is_published) or
            (not obj.category.is_published) or
            (obj.pub_date > timezone.now())
        ):
            raise Http404
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related(
            'author'
        )
        return context


class CategoryListView(PostAddition, ListView):
    template_name = 'blog/category.html'

    def get_queryset(self):
        _category = get_object_or_404(
            Category.objects.filter(
                slug=self.kwargs['category_slug'], is_published=True
            )
        )
        return super().get_queryset().filter(category=_category)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True,
        )
        return context


class ProfileUser(PostAddition, ListView):
    model = Post
    template_name = 'blog/profile.html'

    def get_queryset(self):
        _user = get_object_or_404(
            User.objects.filter(username=self.kwargs['username'])
        )
        if _user == self.request.user:
            return _user.posts.annotate(
                comment_count=Count('comments')
            ).select_related(
                'category', 'author', 'location'
            ).order_by('-pub_date')
        return super().get_queryset().filter(author=_user)

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
        return self.request.user

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class CommentCreateView(LoginRequiredMixin, CommentMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_object(self):
        pass

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(
            Post,
            pk=self.kwargs['post_id'],
            )
        return super().form_valid(form)


class CommentUpdateView(LoginRequiredMixin, CommentMixin, UpdateView):
    pass


class CommentDeleteView(LoginRequiredMixin, CommentMixin, DeleteView):
    pass
