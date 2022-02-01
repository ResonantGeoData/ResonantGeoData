from django.urls import path

from . import views

urlpatterns = [
    path('', views.root, name='stac-root'),
    path('search', views.search, name='stac-search'),
    path('api', views.service_desc, name='stac-service-desc'),
    path('api.html', views.service_doc, name='stac-service-doc'),
    path('conformance', views.conformance, name='stac-conformance'),
    path('collections', views.collections, name='stac-collections'),
    path('collections/<collection_id>', views.collection, name='stac-collection'),
    path('collections/<collection_id>/items', views.items, name='stac-collection-items'),
    path('collections/<collection_id>/items/<item_id>', views.item, name='stac-collection-item'),
]
