from typing import ClassVar

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from apps.auths.managers import UserManager

NAME_MAX_LENGTH = 50


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=NAME_MAX_LENGTH)
    last_name = models.CharField(max_length=NAME_MAX_LENGTH)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: ClassVar[list[str]] = ["first_name", "last_name"]

    def __str__(self) -> str:
        return self.email
