from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone

from blog.forms import CommentForm, PostForm
from blog.models import Comment, Post

VISIBLE_POSTS = 10


class PostAddition:
    paginate_by = VISIBLE_POSTS

    def get_queryset(self):
        return Post.objects.annotate(
            comment_count=Count('comments')
        ).select_related(
            'category', 'location', 'author'
        ).filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now()
        ).order_by('-pub_date')


class PostDispMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.user != self.get_object().author:
            return redirect(
                'blog:post_detail',
                post_id=self.kwargs['post_id']
            )
        return super().dispatch(request, *args, **kwargs)


class PostMixin:
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'


class CommentMixin:
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def get_object(self):
        return get_object_or_404(
            Comment,
            pk=self.kwargs['comment_id'],
            author=self.request.user
        )

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']}
        )
