from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse

from core.models import PublishedModel

User = get_user_model()

SYMBOL_LIMIT = 30


class Category(PublishedModel):
    title = models.CharField('Заголовок', max_length=256)
    description = models.TextField('Описание')
    slug = models.SlugField(
        'Идентификатор',
        unique=True,
        help_text=('Идентификатор страницы для URL; '
                   'разрешены символы латиницы, цифры, дефис и подчёркивание.')
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'

    def __str__(self) -> str:
        return self.title[:SYMBOL_LIMIT]


class Location(PublishedModel):
    name = models.CharField('Название места', max_length=256)

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self) -> str:
        return self.name[:SYMBOL_LIMIT]


class Post(PublishedModel):
    title = models.CharField('Заголовок', max_length=256)
    text = models.TextField('Текст')
    pub_date = models.DateTimeField(
        'Дата и время публикации',
        help_text=('Если установить дату и время в будущем'
                   ' — можно делать отложенные публикации.')
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор публикации',
        on_delete=models.CASCADE
    )
    location = models.ForeignKey(
        Location,
        verbose_name='Местоположение',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    category = models.ForeignKey(
        Category,
        verbose_name='Категория',
        null=True,
        on_delete=models.SET_NULL,
    )
    image = models.ImageField(
        'Фото',
        upload_to='blog_images',
        blank=True
    )

    class Meta:
        default_related_name = 'posts'
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'

    def __str__(self) -> str:
        return self.title[:SYMBOL_LIMIT]

    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.pk})


class Comment(models.Model):
    text = models.TextField('Текст комментария')
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ('created_at',)
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self) -> str:
        return (f'Комментарий автора {self.post.author.username}'
                'к посту {self.post.title}, текст: {self.text}')
