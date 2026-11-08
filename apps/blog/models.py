from django.conf import settings
from django.db import models
from django.utils.text import slugify

CATEGORY_NAME_MAX_LENGTH = 100
TAG_NAME_MAX_LENGTH = 50
POST_TITLE_MAX_LENGTH = 200
STATUS_MAX_LENGTH = 20
SLUG_SUFFIX_START = 2


class Category(models.Model):
    name = models.CharField(max_length=CATEGORY_NAME_MAX_LENGTH, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural = "categories"

    def __str__(self) -> str:
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=TAG_NAME_MAX_LENGTH, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self) -> str:
        return self.name


class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    title = models.CharField(max_length=POST_TITLE_MAX_LENGTH)
    slug = models.SlugField(unique=True, blank=True)
    body = models.TextField()
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts")
    status = models.CharField(
        max_length=STATUS_MAX_LENGTH,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

    def _generate_unique_slug(self) -> str:
        base_slug = slugify(self.title)
        slug = base_slug
        counter = SLUG_SUFFIX_START
        while Post.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Comment by {self.author} on {self.post}"
