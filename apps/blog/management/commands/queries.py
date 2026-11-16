from datetime import timedelta
from typing import Any

from django.db.models import Count
from django.utils import timezone
from django.utils.text import slugify

from apps.auths.models import User
from apps.blog.management.commands.seed import CATEGORY_NAMES, EMAIL_DOMAIN, TAG_NAMES
from apps.blog.models import Post

PREVIEW_ROWS = 5
FIRST_MUTATING_NUMBER = 40
LAST_MUTATING_NUMBER = 44
SAMPLE_PAGE = 2
SAMPLE_DAYS = 30
SAMPLE_PERIOD_DAYS = 90
SAMPLE_CATEGORIES = 2
MIN_TAGS_FOR_PAIR = 2


def tag_pair() -> tuple[str, str]:
    """Slugs of two tags that belong to the same post."""
    post = Post.objects.annotate(tags_total=Count("tags")).filter(tags_total__gte=MIN_TAGS_FOR_PAIR).first()
    if post is None:
        return "", ""
    first, second = post.tags.values_list("slug", flat=True)[:MIN_TAGS_FOR_PAIR]
    return first, second


def sample_arguments() -> dict[int, dict[str, Any]]:
    """Sample argument values for queries that take arguments."""
    newest_post = Post.objects.order_by("-created_at").first()
    post_slug = newest_post.slug if newest_post else ""
    title_word = newest_post.title.split()[0] if newest_post else ""
    created = newest_post.created_at if newest_post else timezone.now()
    author_email = (
        User.objects.filter(posts__status=Post.Status.PUBLISHED).values_list("email", flat=True).first() or ""
    )
    first_tag, second_tag = tag_pair()
    today = timezone.localdate()
    return {
        4: {"slug": post_slug},
        7: {"page": SAMPLE_PAGE},
        8: {"word": title_word},
        9: {"domain": EMAIL_DOMAIN},
        11: {"slugs": [slugify(name) for name in CATEGORY_NAMES[:SAMPLE_CATEGORIES]]},
        12: {"year": created.year, "month": created.month},
        13: {"days": SAMPLE_DAYS},
        14: {"start": today - timedelta(days=SAMPLE_PERIOD_DAYS), "end": today},
        15: {"email": author_email},
        16: {"tag_slug": slugify(TAG_NAMES[0])},
        17: {"category_slug": slugify(CATEGORY_NAMES[0])},
        21: {"first_slug": first_tag, "second_slug": second_tag},
    }
