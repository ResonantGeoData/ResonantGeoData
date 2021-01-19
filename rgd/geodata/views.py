import json

from django.views import generic
from django.views.generic import DetailView

from rgd.geodata import permissions

from .api import search
from .models.common import SpatialEntry
from .models.fmv.base import FMVEntry
from .models.geometry import GeometryEntry
from .models.imagery.base import RasterEntry, RasterMetaEntry


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
        elif 'geojson' in self.request.GET:
            self.search_params = self.request.GET
            method = search.search_geojson_filter
        queryset = self.model.objects.filter(method(self.search_params))
        return permissions.filter_read_perm(self.request.user, queryset)

    def _get_extent_summary(self):
        return search.extent_summary_spatial(self.object_list)

    def get_context_data(self, *args, **kwargs):
        # The returned query set is in self.object_list, not self.queryset
        context = super().get_context_data(*args, **kwargs)
        summary = self._get_extent_summary()
        context['extents'] = json.dumps(summary)
        context['search_params'] = json.dumps(self.search_params)
        # Have a smaller dict of meta fields to parse for menu bar
        # This keeps us from parsing long GeoJSON fields twice
        meta = {
            'count': summary['count'],
        }
        context['extents_meta'] = json.dumps(meta)
        return context


class RasterEntriesListView(_SpatialListView):
    model = RasterMetaEntry
    context_object_name = 'raster_metas'
    template_name = 'geodata/raster_entries.html'


class SpatialEntriesListView(_SpatialListView):
    model = SpatialEntry
    context_object_name = 'spatial_entries'
    template_name = 'geodata/spatial_entries.html'


class GeometryEntriesListView(_SpatialListView):
    model = GeometryEntry
    context_object_name = 'geometries'
    template_name = 'geodata/geometry_entries.html'


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
        image_entries = self.object.image_set.images.all()
        image_urls = {}
        for image_entry in image_entries:
            thumbnail = image_entry.thumbnail
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
        context['frame_rate'] = json.dumps(self.object.fmv_file.frame_rate)
        return context


class GeometryEntryDetailView(_SpatialDetailView):
    model = GeometryEntry

    def _get_extent(self):
        extent = super()._get_extent()
        extent['data'] = self.object.data.json
        return extent


class SpatialEntryDetailView(_SpatialDetailView):
    model = SpatialEntry
