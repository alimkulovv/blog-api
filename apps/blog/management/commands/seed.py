import random
import time
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.utils.text import slugify
from faker import Faker

from apps.blog.models import Category, Post, Tag

User = get_user_model()

DEFAULT_USERS=20
DEFAULT_POSTS = 20
DEFAULT_COMMENTS = 20

SEED_PASSWORD = "SeedPass123!"
EMAIL_DOMAIN = "example.com"

INACTIVE_USER_RATIO = 0.15
STAFF_USER_RATIO = 0.1
PUBLIC_POST_RATIO = 0.7
NO_CATREGORY_POST_RATIO = 0.1

MAXS_TAGS_PER_POST = 5
POST_TITLE_WORDS = 6
POST_PARAGRAPHS = 4
COMMENT_MIN_SENTENCES = 1
COMMENT_MAX_SENTENCES = 3
SLUG_SUFFIX_START = 2
TITLE_MAX_LENGTH = 200

CATEGORY_NAMES = [
    "Python",
    "Django",
    "DevOps",
    "Databases",
    "Frontend",
    "Testing",
    "Security",
    "Career",
]
TAG_NAMES = [
    "api", "rest", "orm", "docker", "git", "linux", "postgres", "redis", "celery", "async", "tips", "tutorial", "performance", "deployment", "refactoring", "ci-cd", "beginners", "architecture", "debugging", "tools",
    ] # fmt: skip

class Command(BaseCommand):
    help = "Fill the database with fake data."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("__users", type=int, default=DEFAULT_USERS, help="Number of users to create.")
        parser.add_argument("__posts", type=int, default=DEFAULT_POSTS, help="Number of posts to create.")
        parser.add_argument("__comments", type=int, default=DEFAULT_COMMENTS, help="Number of comments to create.")
        parser.add_argument("--clear", action="store_true", help="Delete existing before seeding.")

    def handle(self , *args: Any, **options: Any) -> None:
        users_count = options["__users"]
        posts_count = options["__posts"]
        comments_count = options["__comments"]

        if min(users_count, posts_count, comments_count) < 0:
            raise CommandError("Number of users, posts, and comments must be non-negative.")

        started = time.monotonic()
        faker = Faker()

        with transaction.atomic():
            if options["clear"]:
                self._clear()

            users_created = self._create_users(users_count, faker)
            categories_created = self._create_named(Category, CATEGORY_NAMES)
            tags_created = self._create_named(Tag, TAG_NAMES)

            if (posts_count or comments_count) and not User.objects.exists():
                raise CommandError("Cannot create posts or comments: there are no users.")
            posts_created =  self._create_posts(fake , comments_count)

            if comments_count and not Post.objects.filter(status=Post.Status.PUBLISHED).exists():
                raise CommandError("Cannot create comments: there are no published posts.")

            comments_created = self._create_comments(fake , comments_count)

        elapsed = time .monotonic() - started
        self.stdout.write(f"Users:     {users_created:>4} created")
        self.stdout.write(f"Categories: {categories_created:>4} created")
        self.stdout.write(f"Tags:       {tags_created:>4} created")
        self.stdout.write(f"Posts:      {posts_created:>4} created")
        self.stdout.write(f"Comments:   {comments_created:>4} created")
        self.stdout.write(self.style.SUCCESS(f"Done in {elapsed:2f} seconds"))

    def _clear(self) -> None:
        Comment.objects.all().delete()
        Post.objects.all().delete()
        Tag.objects.all().delete()
        Category.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write("Existing deleted(superusers kept).")

    def _create_users(self, fake: Faker, count: int) -> int:
        used_emails = set(User.objects.values_list("email", flat=True))
        hashed_password = make_password(SEED_PASSWORD)
        users = []
        for _ in range(count):
            first_name = fake.first_name()
            last_name = fake.last_name()
            base = f"{first_name.lower()}.{last_name.lower()}"
            email = f"{base}@{EMAIL_DOMAIN}"
            while email in used_emails:
                email = f"{base}{suffix}@{EMAIL_DOMAIN}"
                suffix += 1
            used_emails.add(email)
            users_append(
                User(
                    email=email,
                    first_name = first_name,
                    last_name = last_name,
                    password = hashed_password,
                    is_active = random.random() > INACTIVE_USER_RATIO,
                    is_staff = random.random() < STAFF_USER_RATIO,

                )
            )
        return len(User.objects.bulk_create(users))

    def _create_named(self , model: type[Category | Tag], names: list[str]) -> int:
        existing = set(model.objects.values_list("name", flat=True))
        used_slugs = set(model.objects.values_list("slug", flat=True))
        objects = []
        for name in names:
            slug = slugify(name)
            if name in existing or slug in used_slugs:
                continue
            objects.append(model(name=name, slug=slug))
        return len(model.objects.bulk_create(objects))

    def _create_posts(self, fake: Faker, count: int) -> int:
        if not count:
            return 0

        user_ids = list(User.objects.values_list("id", flat=True))
        category_ids = list(Category.objects.values_list("id", flat=True))
        tag_ids = list(Tag.objects.values_list("id", flat=True))
        used_slugs = set(Post.objects.values_list("slug", flat=True))

        posts = []
        for _ in range(count):
            title = fake.sentence(nb_words=POST_TITLE_WORDS).rstrip(".")[:TITLE_MAX_LENGTH]
            base_slug = slugify(title)
            slug = base_slug
            suffix = SLUG_SUFFIX_START
            while slug in used_slugs:
                slug = f"{base_slug}-{suffix}"
                suffix += 1
            used_slugs.add(slug)

            has_category = category_ids and random.random() > NO_CATREGORY_RATIO
            is_published = random.random() < PUBLIC_POST_RATIO
            posts.append(
                Post(
                    author_id=random.choice(user_ids),
                    title=title,
                    slug=slug,
                    body="\n\n".join(fake.paragraphs(nb=POST_PARAGRAPHS)),
                    category_id=random.choice(category_ids) if has_category else None,
                    status=Post.Status.PUBLISHED if is_published else Post.Status.DRAFT,
                )
            )
        created_posts = Post.objects.bulk_create(posts)
        for post in created:
            tags_number = random .randint(0, min(MAXS_TAGS_PER_POST, len(tag_ids)))
            post.tags.set(random.sample(tags, tags_number))
        return len(created)

    def _create_comments(self, fake: Faker, count: int) -> int:
        if not count:
            return 0
        user_ids = list(User.objects.values_list("id", flat=True))
        post_ids = list(Post.objects.filter(status=Post.Status.PUBLISHED).values_list("id", flat=True))
        comments = [
            Comment(
            post_id=random.choice(post_ids),
            author_id=random.choice(user_ids),
            body=" ".join(fake.sentences(nb=random.randint(COMMENT_MIN_SENTENCES, COMMENT_MAX_SENTENCES))),
        )

        for _ in range(count)
    ]
    return len(Comment.objects.bulk_create(comments))



