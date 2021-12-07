import pytest
from rest_framework.authtoken.views import ObtainAuthToken
from rgd import models
from rgd.permissions import filter_read_perm, filter_write_perm
from rgd.rest.mixins import BaseRestViewMixin
from rgd.urls import urlpatterns
from rgd.views import PermissionDetailView, PermissionListView, PermissionTemplateView


@pytest.mark.django_db(transaction=True)
def test_unassigned_permissions_complex(
    user_factory, user, spatial_asset_a, spatial_asset_b, settings
):
    # TODO: reimplement with multi raster file fixture also
    settings.RGD_GLOBAL_READ_ACCESS = False
    admin = user_factory(is_superuser=True)
    admin_q = filter_read_perm(admin, models.SpatialEntry.objects.all())
    basic_q = filter_read_perm(user, models.SpatialEntry.objects.all())
    assert len(admin_q) == 2
    assert len(basic_q) == 0
    settings.RGD_GLOBAL_READ_ACCESS = True
    admin_q = filter_read_perm(admin, models.SpatialEntry.objects.all())
    basic_q = filter_read_perm(user, models.SpatialEntry.objects.all())
    assert len(admin_q) == len(basic_q)
    assert set(admin_q) == set(basic_q)


@pytest.mark.django_db(transaction=True)
def test_nonadmin_user_permissions(user, spatial_asset_a, spatial_asset_b):
    # Filter and make sure nothing returns
    basic_q = filter_read_perm(user, models.SpatialEntry.objects.all())
    assert basic_q.count() == 0
    # Set collection on files and make sure both return
    collection = models.Collection.objects.create(name='test')
    permission = models.CollectionPermission.objects.create(
        collection=collection, user=user, role=models.CollectionPermission.READER
    )
    spatial_asset_a.files.update(collection=collection)
    spatial_asset_b.files.update(collection=collection)
    read_q = filter_read_perm(user, models.SpatialEntry.objects.all())
    assert read_q.count() == 2
    # Now make sure this user does not have write access
    write_q = filter_write_perm(user, models.SpatialEntry.objects.all())
    assert write_q.count() == 0
    # Update permissions to have write access and check
    permission.role = models.CollectionPermission.OWNER
    permission.save(
        update_fields=[
            'role',
        ]
    )
    write_q = filter_write_perm(user, models.SpatialEntry.objects.all())
    assert write_q.count() == 2


@pytest.mark.django_db(transaction=True)
def test_nonadmin_created_by_permissions(user, spatial_asset_a, spatial_asset_b):
    # Filter and make sure nothing returns
    q = filter_read_perm(user, models.SpatialEntry.objects.all())
    assert q.count() == 0
    # Update the `created_by` field and check that query works
    spatial_asset_a.files.update(created_by=user)
    spatial_asset_b.files.update(created_by=user)
    # NOTE: the ChecksumFileFactory sets the Collection by default
    q = filter_read_perm(user, models.SpatialEntry.objects.all())
    assert q.count() == 2
    # Update the `collection` field and check that query works
    spatial_asset_a.files.update(collection=None)
    spatial_asset_b.files.update(collection=None)
    q = filter_read_perm(user, models.SpatialEntry.objects.all())
    assert q.count() == 2


def test_urls():
    for pattern in urlpatterns:
        if hasattr(pattern.callback, 'view_class') and 'WrappedAPIView' not in str(
            pattern.callback
        ):
            assert issubclass(
                pattern.callback.view_class,
                (
                    BaseRestViewMixin,
                    PermissionDetailView,
                    PermissionTemplateView,
                    PermissionListView,
                    ObtainAuthToken,
                ),
            )
