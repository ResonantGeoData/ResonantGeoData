import json
import os

from django.db.models.fields.files import FieldFile
from django.http import HttpResponse
from django.shortcuts import get_object_or_404  # , render
from django.utils.encoding import smart_str
from django.views import generic
from django.views.generic import DetailView
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view

from . import models, search
from .models.common import SpatialEntry
from .models.fmv.base import FMVEntry
from .models.imagery.base import RasterEntry, Thumbnail


class _SpatialListView(generic.ListView):
    def get_queryset(self):
        # latitude, longitude, radius, time, timespan, and timefield
        self.search_params = {}
        point = {'longitude', 'latitude', 'radius'}
        bbox = {'minimum_longitude', 'minimum_latitude', 'maximum_longitude', 'maximum_latitude'}
        search_options = point.union(bbox)
        # Collect all passed search options
        for key in search_options:
            if self.request.GET.get(key):
                try:
                    self.search_params[key] = float(self.request.GET.get(key))
                except ValueError:
                    pass
        # Choose search method based on passed options
        method = search.search_near_point_filter
        if all(k in self.search_params for k in point):
            method = search.search_near_point_filter
        elif all(k in self.search_params for k in bbox):
            method = search.search_bounding_box_filter

        return self.model.objects.filter(method(self.search_params))

    def _get_extent_summary(self):
        return search.extent_summary_spatial(self.object_list)

    def get_context_data(self, *args, **kwargs):
        # The returned query set is in self.object_list, not self.queryset
        context = super().get_context_data(*args, **kwargs)
        context['extents'] = json.dumps(self._get_extent_summary())
        context['search_params'] = json.dumps(self.search_params)
        return context


class RasterEntriesListView(_SpatialListView):
    model = RasterEntry
    context_object_name = 'rasters'
    template_name = 'geodata/raster_entries.html'


class SpatialEntriesListView(_SpatialListView):
    model = SpatialEntry
    context_object_name = 'spatial_entries'
    template_name = 'geodata/spatial_entries.html'


class FMVEntriesListView(_SpatialListView):
    model = FMVEntry
    context_object_name = 'entries'
    template_name = 'geodata/fmv_entries.html'

    def _get_extent_summary(self):
        return search.extent_summary_fmv(self.object_list)


class _SpatialDetailView(DetailView):
    def _get_extent(self):
        if self.object.footprint is None:
            extent = {
                'count': 0,
            }
        else:
            extent = {
                'count': 1,
                'collect': self.object.footprint.json,
                'outline': self.object.outline.json,
                'extent': {
                    'xmin': self.object.footprint.extent[0],
                    'ymin': self.object.footprint.extent[1],
                    'xmax': self.object.footprint.extent[2],
                    'ymax': self.object.footprint.extent[3],
                },
            }
        return extent

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['extents'] = json.dumps(self._get_extent())
        context['search_params'] = json.dumps({})
        return context


class RasterEntryDetailView(_SpatialDetailView):
    model = RasterEntry

    def _get_extent(self):
        extent = super()._get_extent()
        # Add a thumbnail of the first image in the raster set
        image_entries = self.object.images.all()
        image_urls = {}
        for image_entry in image_entries:
            thumbnail = Thumbnail.objects.filter(image_entry=image_entry).first()
            image_urls[thumbnail.image_entry.id] = thumbnail.base_thumbnail.url
        extent['thumbnails'] = image_urls
        return extent


class FMVEntryDetailView(_SpatialDetailView):
    model = FMVEntry

    def _get_extent(self):
        extent = super()._get_extent()
        if self.object.ground_union is not None:
            # All or none of these will be set, only check one
            extent['collect'] = self.object.ground_union.json
            extent['ground_frames'] = self.object.ground_frames.json
            extent['frame_numbers'] = self.object._blob_to_array(self.object.frame_numbers)
        return extent

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['frame_rate'] = json.dumps(self.object.frame_rate)
        return context


@swagger_auto_schema(
    method='GET',
    operation_summary='Download a model file',
    operation_description='Download a model file through the server instead of from the assetstore',
)
@api_view(['GET'])
def download_file(request, model, id, field):
    model_class = ''.join([part[:1].upper() + part[1:] for part in model.split('_')])
    if not hasattr(models, model_class):
        raise Exception('No such model (%s)' % model)
    model_inst = get_object_or_404(getattr(models, model_class), pk=id)
    if not isinstance(getattr(model_inst, field, None), FieldFile):
        raise Exception('No such file (%s)' % field)
    file = getattr(model_inst, field)
    filename = os.path.basename(file.name)
    if not filename:
        filename = '%s_%s_%s.dat' % (model, id, field)
    mimetype = getattr(
        model_inst,
        '%s_mimetype' % field,
        'text/plain' if field == 'log' else 'application/octet-stream',
    )
    response = HttpResponse(file.chunks(), content_type=mimetype)
    response['Content-Disposition'] = smart_str(u'attachment; filename=%s' % filename)
    if len(file) is not None:
        response['Content-Length'] = len(file)
    return response
