from django.contrib import admin
from django.db.models import Count, QuerySet
from django.http import HttpRequest
from unfold.admin import ModelAdmin
from unfold.decorators import display
from unfold.sections import TableSection
from unfold.contrib.filters.admin import AutocompleteSelectFilter, RangeDateTimeFilter
from django.utils.text import Truncator

from apps.blog.models import Category, Tag , Comment , Post


class CategoryPostsSection(TableSection):
    verbose_name = "Posts"
    related_name = "posts"
    fields = ["title", "status", "created_at"]


class PostsCountMixin:
    @display(description="Posts", ordering="posts_count")
    def posts_count(self, obj: Category | Tag) -> int:
        return obj.posts_count

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return super().get_queryset(request).annotate(posts_count=Count("posts"))


@admin.register(Category)
class CategoryAdmin(PostsCountMixin, ModelAdmin):
    list_display = ["name", "slug", "posts_count"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}
    list_sections = [CategoryPostsSection]


@admin.register(Tag)
class TagAdmin(PostsCountMixin, ModelAdmin):
    list_display = ["name", "slug", "posts_count"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Post)
class PostAdmin(ModelAdmin):
    search_fields = ["title"]


@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    list_display = ["post_title", "author", "body_preview", "created_at"]
    list_filter = [
        ("post", AutocompleteSelectFilter),
        ("author", AutocompleteSelectFilter),
        ("created_at", RangeDateTimeFilter),
    ]
    list_filter_submit = True
    list_select_related = ["post", "author"]
    search_fields = ["body", "author__email", "post__title"]
    autocomplete_fields = ["post", "author"]

    @display(description="Post", ordering="post__title")
    def post_title(self, obj: Comment) -> str:
        return obj.post.title

    @display(description="Body")
    def body_preview(self, obj: Comment) -> str:
        return Truncator(obj.body).chars(COMMENT_BODY_PREVIEW_LENGTH)

COMMENT_BODY_PREVIEW_LENGTH = 50
