from django.contrib import admin, messages
from django.db import models
from django.db.models import Count, QuerySet
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.text import Truncator
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import (
    AutocompleteSelectFilter,
    ChoicesDropdownFilter,
    MultipleRelatedDropdownFilter,
    RangeDateTimeFilter,
    RelatedDropdownFilter,
)
from unfold.contrib.forms.widgets import WysiwygWidget
from unfold.decorators import action, display
from unfold.sections import TableSection

from apps.blog.models import Category, Comment, Post, Tag

COMMENT_BODY_PREVIEW_LENGTH = 50
COMMENTS_PER_PAGE = 10
POST_LIST_URL_NAME = "admin:blog_post_changelist"
COMMENT_LIST_URL_NAME = "admin:blog_comment_changelist"


class CategoryPostsSection(TableSection):
    verbose_name = "Posts"
    related_name = "posts"
    fields = ["title", "status", "created_at"]


class PostCommentsSection(TableSection):
    verbose_name = "Comments"
    related_name = "comments"
    fields = ["author", "body", "created_at"]


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


class CommentInline(TabularInline):
    model = Comment
    tab = True
    per_page = COMMENTS_PER_PAGE
    extra = 0
    autocomplete_fields = ["author"]


@admin.register(Post)
class PostAdmin(ModelAdmin):
    list_display = [
        "post_header",
        "status_label",
        "category",
        "tags_dropdown",
        "comments_count",
        "created_at",
    ]
    list_filter = [
        ("status", ChoicesDropdownFilter),
        ("category", RelatedDropdownFilter),
        ("tags", MultipleRelatedDropdownFilter),
        ("author", AutocompleteSelectFilter),
        ("created_at", RangeDateTimeFilter),
    ]
    list_filter_submit = True
    search_fields = ["title", "body", "author__email"]
    list_sections = [PostCommentsSection]

    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ["author", "category", "tags"]
    readonly_fields = ["created_at", "updated_at"]
    formfield_overrides = {models.TextField: {"widget": WysiwygWidget}}
    warn_unsaved_form = True
    inlines = [CommentInline]

    fieldsets = (
        ("Content", {"classes": ["tab"], "fields": ("title", "slug", "body")}),
        ("Classification", {"classes": ["tab"], "fields": ("category", "tags", "status")}),
        ("Meta", {"classes": ["tab"], "fields": ("author", "created_at", "updated_at")}),
    )

    actions = ["publish_selected", "move_to_drafts"]
    actions_row = ["toggle_publish"]
    actions_list = ["publish_all_drafts"]
    actions_detail = ["open_comments"]
    actions_submit_line = ["save_and_publish"]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Post]:
        return (
            super()
            .get_queryset(request)
            .select_related("author", "category")
            .prefetch_related("tags")
            .annotate(comments_total=Count("comments", distinct=True))
        )
    @display(description="Post", header=True)
    def post_header(self, obj: Post) -> list[str]:
        return [obj.title, obj.author.get_full_name() if hasattr(obj.author, "get_full_name") else str(obj.author)]

    @display(
        description="Status",
        label={Post.Status.PUBLISHED: "success", Post.Status.DRAFT: "warning"},
    )
    def status_label(self, obj: Post) -> tuple[str, str]:
        return obj.status, obj.get_status_display()

    @display(description="Tags", dropdown=True)
    def tags_dropdown(self, obj: Post) -> dict:
        tags = obj.tags.all()
        return {
            "title": str(len(tags)),
            "items": [{"title": tag.name} for tag in tags],
        }

    @display(description="Comments", ordering="comments_total")
    def comments_count(self, obj: Post) -> int:
        return obj.comments_total

    # --- bulk actions ---
    @action(description="Publish selected")
    def publish_selected(self, request: HttpRequest, queryset: QuerySet[Post]) -> None:
        updated = queryset.update(status=Post.Status.PUBLISHED, updated_at=timezone.now())
        self.message_user(request, f"Published posts: {updated}", messages.SUCCESS)

    @action(description="Move to drafts")
    def move_to_drafts(self, request: HttpRequest, queryset: QuerySet[Post]) -> None:
        updated = queryset.update(status=Post.Status.DRAFT, updated_at=timezone.now())
        self.message_user(request, f"Moved to drafts: {updated}", messages.SUCCESS)

    # --- row action ---
    @action(description="Publish / unpublish", url_path="toggle-publish")
    def toggle_publish(self, request: HttpRequest, object_id: str) -> HttpResponseRedirect:
        post = get_object_or_404(Post, pk=object_id)
        if post.status == Post.Status.PUBLISHED:
            post.status = Post.Status.DRAFT
        else:
            post.status = Post.Status.PUBLISHED


    @action(description="Publish all drafts", url_path="publish-all-drafts")
    def publish_all_drafts(self, request: HttpRequest) -> HttpResponseRedirect:
        updated = Post.objects.filter(status=Post.Status.DRAFT).update(
            status=Post.Status.PUBLISHED,
            updated_at=timezone.now(),
        )
        self.message_user(request, f"Published drafts: {updated}", messages.SUCCESS)
        return redirect(reverse(POST_LIST_URL_NAME))

    @action(description="Open comments", url_path="open-comments")
    def open_comments(self, request: HttpRequest, object_id: str) -> HttpResponseRedirect:
        return redirect(f"{reverse(COMMENT_LIST_URL_NAME)}?post__id__exact={object_id}")

    @action(description="Save & publish")
    def save_and_publish(self, request: HttpRequest, obj: Post) -> None:
        obj.status = Post.Status.PUBLISHED
        obj.save(update_fields=["status", "updated_at"])
