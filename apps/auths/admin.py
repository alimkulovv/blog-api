from django.contrib import admin, messages
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.db.models import Count, QuerySet
from django.http import HttpRequest
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import BooleanRadioFilter
from unfold.decorators import action, display
from unfold.forms import AdminPasswordChangeForm
from unfold.forms import UserChangeForm as BaseUserChangeForm
from unfold.forms import UserCreationForm as BaseUserCreationForm

from apps.auths.models import User

STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"
STAFF_YES = "staff"
STAFF_NO = "not_staff"

admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass


class UserCreationForm(BaseUserCreationForm):
    class Meta(BaseUserCreationForm.Meta):
        model = User
        fields = ("email", "first_name", "last_name")
        field_classes = {}


class UserChangeForm(BaseUserChangeForm):
    class Meta(BaseUserChangeForm.Meta):
        model = User
        fields = "__all__"
        field_classes = {}


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    ordering = ["email"]
    list_display = ["user_header", "is_active_label", "is_staff_label", "posts_count"]
    list_filter = [
        ("is_active", BooleanRadioFilter),
        ("is_staff", BooleanRadioFilter),
    ]
    search_fields = ["email", "first_name", "last_name"]
    actions = ["activate_users", "deactivate_users"]

    fieldsets = (
        (
            "Personal info",
            {"classes": ["tab"], "fields": ("email", "password", "first_name", "last_name")},
        ),
        (
            "Permissions",
            {
                "classes": ["tab"],
                "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
            },
        ),
        ("Important dates", {"classes": ["tab"], "fields": ("last_login",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ["wide"],
                "fields": ("email", "first_name", "last_name", "password1", "password2"),
            },
        ),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[User]:
        return super().get_queryset(request).annotate(posts_count=Count("posts"))

    @display(description="User", header=True)
    def user_header(self, obj: User) -> list[str]:
        initials = f"{obj.first_name[:1]}{obj.last_name[:1]}".upper()
        return [f"{obj.first_name} {obj.last_name}", obj.email, initials]

    @display(
        description="Active",
        label={STATUS_ACTIVE: "success", STATUS_INACTIVE: "danger"},
    )
    def is_active_label(self, obj: User) -> tuple[str, str]:
        if obj.is_active:
            return STATUS_ACTIVE, "Active"
        return STATUS_INACTIVE, "Inactive"

    @display(
        description="Staff",
        label={STAFF_YES: "info", STAFF_NO: "warning"},
    )
    def is_staff_label(self, obj: User) -> tuple[str, str]:
        if obj.is_staff:
            return STAFF_YES, "Staff"
        return STAFF_NO, "Not staff"

    @display(description="Posts", ordering="posts_count")
    def posts_count(self, obj: User) -> int:
        return obj.posts_count

    @action(description="Activate selected users")
    def activate_users(self, request: HttpRequest, queryset: QuerySet[User]) -> None:
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Activated users: {updated}", messages.SUCCESS)

    @action(description="Deactivate selected users")
    def deactivate_users(self, request: HttpRequest, queryset: QuerySet[User]) -> None:
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated users: {updated}", messages.SUCCESS)
