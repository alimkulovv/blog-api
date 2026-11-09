from django.urls import reverse_lazy

from settings.conf import ALLOWED_HOSTS, BASE_DIR, ENV_ID, SECRET_KEY  # noqa: F401

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.auths",
    "apps.blog",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "settings.urls"
WSGI_APPLICATION = "settings.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "auths.User"

UNFOLD = {
    "SITE_TITLE": "Blog API",
    "SITE_HEADER": "Blog API",
    "SITE_SUBHEADER": "Content management",
    "SITE_SYMBOL": "article",
    "COLORS": {
        "primary": {
            "50": "oklch(97% 0.014 254.604)",
            "100": "oklch(93.2% 0.032 255.585)",
            "200": "oklch(88.2% 0.059 254.128)",
            "300": "oklch(80.9% 0.105 251.813)",
            "400": "oklch(70.7% 0.165 254.624)",
            "500": "oklch(62.3% 0.214 259.815)",
            "600": "oklch(54.6% 0.245 262.881)",
            "700": "oklch(48.8% 0.243 264.376)",
            "800": "oklch(42.4% 0.199 265.638)",
            "900": "oklch(37.9% 0.146 265.522)",
            "950": "oklch(28.2% 0.091 267.935)",
        },
    },
    "ENVIRONMENT": "apps.blog.callbacks.environment_callback",
    "SITE_DROPDOWN": [
        {"icon": "code", "title": "GitHub", "link": "https://github.com/alimkulovv/blog-api"},
        {"icon": "menu_book", "title": "Unfold docs", "link": "https://unfoldadmin.com/docs/"},
    ],
    "COMMAND": {"search_models": True, "show_history": True},
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Overview",
                "items": [
                    {"title": "Dashboard", "icon": "dashboard", "link": reverse_lazy("admin:index")},
                ],
            },
            {
                "title": "Content",
                "items": [
                    {
                        "title": "Posts",
                        "icon": "article",
                        "link": reverse_lazy("admin:blog_post_changelist"),
                        "badge": "apps.blog.callbacks.drafts_badge",
                    },
                    {"title": "Comments", "icon": "chat", "link": reverse_lazy("admin:blog_comment_changelist")},
                    {"title": "Categories", "icon": "category", "link": reverse_lazy("admin:blog_category_changelist")},
                    {"title": "Tags", "icon": "sell", "link": reverse_lazy("admin:blog_tag_changelist")},
                ],
            },
            {
                "title": "Users & Access",
                "items": [
                    {
                        "title": "Users",
                        "icon": "person",
                        "link": reverse_lazy("admin:auths_user_changelist"),
                        "permission": "apps.blog.callbacks.superuser_only",
                    },
                    {
                        "title": "Groups",
                        "icon": "group",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                        "permission": "apps.blog.callbacks.superuser_only",
                    },
                ],
            },
        ],
    },
        "TABS": [
        {
            "models": ["blog.post"],
            "items": [
                {"title": "All", "link": reverse_lazy("admin:blog_post_changelist")},
                {"title": "Published", "link": "apps.blog.callbacks.published_tab_link"},
                {"title": "Drafts", "link": "apps.blog.callbacks.drafts_tab_link"},
            ],
        },
    ],
}
