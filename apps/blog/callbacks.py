from django.http import HttpRequest
from django.urls import reverse

from apps.blog.models import Post
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
