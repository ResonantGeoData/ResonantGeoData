from django.urls import path

from . import views

urlpatterns = [
    path(
        '',
        views.CoreView.as_view(),
        name='stac-core',
    ),
    path(
        'search',
        views.SimpleSearchView.as_view(),
        name='stac-search',
    ),
    path(
        'collection/<collection_id>',
        views.CollectionView.as_view(),
        name='stac-collection',
    ),
    path(
        'collection/<collection_id>/items',
        views.ItemCollectionView.as_view(),
        name='stac-collection-items',
    ),
    path(
        'collection/<collection_id>/items/<item_id>',
        views.ItemView.as_view(),
        name='stac-collection-item',
    ),
]
