from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from django.utils.translation import gettext_lazy as _

from accounts.models import Discipline, Tournament, TournamentPlayer, User


class UserAdminCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email",)


class UserAdminChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = "__all__"


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    add_form = UserAdminCreationForm
    form = UserAdminChangeForm
    change_password_form = AdminPasswordChangeForm
    ordering = ("email",)
    list_display = ("email", "is_active", "is_staff", "is_superuser", "date_joined")
    search_fields = ("email",)
    list_filter = ("is_active", "is_staff", "is_superuser")
    filter_horizontal = ("groups", "user_permissions")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Permissions"),
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "is_active", "is_staff", "is_superuser"),
            },
        ),
    )


class TournamentPlayerInline(admin.TabularInline):
    model = TournamentPlayer
    extra = 0
    filter_horizontal = ("selected_disciplines",)
    autocomplete_fields = ("user",)


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ("id", "invite_code", "status", "host", "start_time", "end_time", "result")
    list_filter = ("status", "start_time")
    search_fields = ("invite_code", "host__email")
    autocomplete_fields = ("host",)
    filter_horizontal = ("disciplines",)
    readonly_fields = ("invite_code", "created_at")
    inlines = [TournamentPlayerInline]


@admin.register(Discipline)
class DisciplineAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name", "description")


@admin.register(TournamentPlayer)
class TournamentPlayerAdmin(admin.ModelAdmin):
    list_display = ("id", "tournament", "user", "is_ready", "joined_at")
    list_filter = ("is_ready",)
    search_fields = ("user__email", "tournament__invite_code")
    filter_horizontal = ("selected_disciplines",)
    autocomplete_fields = ("tournament", "user")
