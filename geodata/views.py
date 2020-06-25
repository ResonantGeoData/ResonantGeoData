# from django.shortcuts import render
from django.views import generic
from django.views.generic import DetailView

from .models.raster.base import RasterEntry


class RasterEntriesListView(generic.ListView):
    model = RasterEntry
    context_object_name = 'rasters'
    queryset = RasterEntry.objects.all()
    template_name = 'geodata/raster_entries.html'


class RasterEntryDetailView(DetailView):
    model = RasterEntry
