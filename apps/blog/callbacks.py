import json
from typing import Any

from django.db.models import Count
from django.http import HttpRequest
from django.urls import reverse

from apps.auths.models import User
from apps.blog.models import Category, Comment, Post
from settings.conf import ENV_ID

PROD_ENV_ID = "prod"
POST_LIST_URL_NAME = "admin:blog_post_changelist"


def environment_callback(request: HttpRequest) -> list[str]:
    if ENV_ID == PROD_ENV_ID:
        return ["Production", "danger"]
    return ["Local", "warning"]


def drafts_badge(request: HttpRequest) -> int:
    return Post.objects.filter(status=Post.Status.DRAFT).count()


def superuser_only(request: HttpRequest) -> bool:
    return request.user.is_superuser


def published_tab_link(request: HttpRequest) -> str:
    return f"{reverse(POST_LIST_URL_NAME)}?status__exact={Post.Status.PUBLISHED}"


def drafts_tab_link(request: HttpRequest) -> str:
    return f"{reverse(POST_LIST_URL_NAME)}?status__exact={Post.Status.DRAFT}"

TOP_AUTHORS_LIMIT = 5
PERCENT = 100


def dashboard_callback(request: HttpRequest, context: dict[str, Any]) -> dict[str, Any]:
    published = Post.objects.filter(status=Post.Status.PUBLISHED).count()
    drafts = Post.objects.filter(status=Post.Status.DRAFT).count()
    total_posts = published + drafts

    categories = Category.objects.annotate(posts_total=Count("posts")).order_by("name")
    chart = {
        "labels": [category.name for category in categories],
        "datasets": [
            {
                "label": "Posts",
                "data": [category.posts_total for category in categories],
                "backgroundColor": "#3b82f6",
            }
        ],
    }

    top_authors = User.objects.annotate(posts_total=Count("posts")).order_by("-posts_total")[:TOP_AUTHORS_LIMIT]

    context.update(
        {
            "cards": [
                {"title": "Users", "value": User.objects.count()},
                {"title": "Published posts", "value": published},
                {"title": "Drafts", "value": drafts},
                {"title": "Comments", "value": Comment.objects.count()},
            ],
            "chart_data": json.dumps(chart),
            "authors_table": {
                "headers": ["Author", "Email", "Posts"],
                "rows": [[f"{u.first_name} {u.last_name}", u.email, u.posts_total] for u in top_authors],
            },
            "published_percent": round(published * PERCENT / total_posts) if total_posts else 0,
            "drafts_percent": round(drafts * PERCENT / total_posts) if total_posts else 0,
        }
    )
    return context
