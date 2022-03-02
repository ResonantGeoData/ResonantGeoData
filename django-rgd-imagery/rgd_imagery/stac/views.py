from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.utils.urls import replace_query_param
from rgd.models import Collection
from rgd.permissions import filter_read_perm

from . import querysets, serializers


def paginate_queryset(queryset, request):
    page = int(request.query_params.get('page', 1))
    limit = int(request.query_params.get('limit', 10))
    return queryset.order_by('stac_id')[(page - 1) * limit : page * limit]


def add_page_links(data, values, request):
    page = int(request.query_params.get('page', 1))
    limit = int(request.query_params.get('limit', 10))
    if len(values) < limit:
        return data
    url = request.build_absolute_uri()
    next_link = replace_query_param(url, 'page', page + 1)
    if 'links' not in data:
        data['links'] = []
    data['links'].append({'rel': 'next', 'href': next_link})


@api_view()
def root(request):
    queryset = filter_read_perm(request.user, Collection.objects.all())
    values = [*queryset.values('id', 'name')]
    values.append({'id': 'default', 'name': 'default'})
    data = serializers.get_root(values, request)
    return Response(data)


@api_view()
def collection(request, collection_id):
    queryset = querysets.collection.get_queryset(
        user=request.user,
        pk=collection_id,
    )
    data = serializers.get_collection(queryset.get(), request)
    return Response(data)


@api_view()
def collections(request):
    queryset = querysets.collection.get_queryset(user=request.user)
    queryset = paginate_queryset(queryset, request)
    values = [*queryset]
    data = serializers.get_collections(values, request)
    add_page_links(data, values, request)
    return Response(data)


@api_view()
def item(request, collection_id, item_id):
    queryset = querysets.item.get_queryset(
        user=request.user,
        pk=item_id,
        collection=collection_id,
    )
    data = serializers.get_item(queryset.get(), request)
    return Response(data)


@api_view()
def items(request, collection_id):
    queryset = querysets.item.get_queryset(
        user=request.user,
        collection=collection_id,
        bbox=request.query_params.get('bbox'),
        intersects=request.query_params.get('intersects'),
        ids=request.query_params.get('ids'),
        collections=request.query_params.get('collections'),
        datetime=request.query_params.get('datetime'),
    )
    queryset = paginate_queryset(queryset, request)
    values = [*queryset]
    data = serializers.get_items(values, request)
    add_page_links(data, values, request)
    return Response(data)


@api_view()
def search(request):
    queryset = querysets.item.get_queryset(
        user=request.user,
        bbox=request.query_params.get('bbox'),
        intersects=request.query_params.get('intersects'),
        ids=request.query_params.get('ids'),
        collections=request.query_params.get('collections'),
        datetime=request.query_params.get('datetime'),
    )
    queryset = paginate_queryset(queryset, request)
    values = [*queryset]
    data = serializers.get_items(values, request)
    add_page_links(data, values, request)
    return Response(data)


@api_view()
def conformance(request):
    data = serializers.get_conformance(request)
    return Response(data)


@api_view()
def service_desc(request):
    data = serializers.get_service_desc(request)
    return Response(data)


@api_view()
def service_doc(request):
    data = serializers.get_service_desc(request)
    return Response(data)
