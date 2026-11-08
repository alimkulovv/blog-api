#!/usr/bin/env python
import os
import sys
from pathlib import Path

from decouple import Config, RepositoryEnv

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / "settings" / ".env"
DEFAULT_ENV_ID = "local"


def main() -> None:
    env = Config(RepositoryEnv(ENV_FILE))
    env_id = env("BLOG_ENV_ID", default=DEFAULT_ENV_ID)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"settings.env.{env_id}")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("Django is not installed. Activate your virtualenv.") from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
