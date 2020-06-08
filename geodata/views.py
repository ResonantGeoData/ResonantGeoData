# from django.shortcuts import render
from django.views import generic

from .models.raster.base import RasterEntry


class RasterEntriesListView(generic.ListView):
    model = RasterEntry
    context_object_name = 'rasters'
    queryset = RasterEntry.objects.all()
    template_name = 'geodata/raster_entries.html'
