from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib.gis.admin import OSMGeoAdmin
from rgd.models import SpatialAsset, WhitelistedEmail

from .mixins import MODIFIABLE_FILTERS, _FileGetNameMixin


def make_users_active(modeladmin, request, queryset):
    """Make each user active."""
    for user in queryset.all():
        if not user.is_active:
            user.is_active = True
            user.save(update_fields=['is_active'])


def make_users_staff(modeladmin, request, queryset):
    """Make each user staff."""
    for user in queryset.all():
        if not user.is_staff:
            user.is_staff = True
            user.save(update_fields=['is_staff'])


admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    actions = (
        make_users_active,
        make_users_staff,
    )

    list_display = (
        'username',
        'is_staff',
        'is_superuser',
        'is_active',
    )


@admin.register(WhitelistedEmail)
class WhitelistedEmailAdmin(OSMGeoAdmin):
    list_display = (
        'pk',
        'email',
    )


@admin.register(SpatialAsset)
class SpatialAssetAdmin(OSMGeoAdmin, _FileGetNameMixin):
    list_display = (
        'pk',
        'get_name',
        'modified',
        'created',
    )
    list_filter = MODIFIABLE_FILTERS
    raw_id_fields = ('files',)
