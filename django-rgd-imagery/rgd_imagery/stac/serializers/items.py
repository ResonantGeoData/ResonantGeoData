from .item import get_item


# https://github.com/radiantearth/stac-api-spec/blob/master/ogcapi-features/README.md
def get_items(queryset, request):
    return {
        'type': 'FeatureCollection',
        'features': [get_item(item, request) for item in queryset],
    }
