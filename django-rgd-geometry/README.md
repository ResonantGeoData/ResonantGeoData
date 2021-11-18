[![logo](https://raw.githubusercontent.com/ResonantGeoData/ResonantGeoData/main/logos/RGD_Logo.png)](https://github.com/ResonantGeoData/ResonantGeoData/)

# Resonant GeoData Geometry

[![PyPI](https://img.shields.io/pypi/v/django-rgd-geometry.svg?logo=python&logoColor=white)](https://pypi.org/project/django-rgd-geometry/)

A submodule of Resonant GeoData for storing shapefiles.


## Installation

Follow the instructions for the core `django-rgd` app first, then

```
pip install --find-links https://girder.github.io/large_image_wheels django-rgd-geometry
```

Add this app to your `INSTALLED_APPS` along with the core RGD app:

```py
INSTALLED_APPS += [
    'django.contrib.gis',
    'rgd',
    'rgd_geometry',
]
```


## Models

This app adds a few additional models on top of the core app for storing geometry data

- `GeometryArchive`: the base data model for ingesting shapefile data. This will run a background task to pull out all vector geometry from an uploaded archive to generate a new `Geometry` record.
- `Geometry`: A place to store a collection of vector geometry. This can be manually created without a shapefile.


## Management Commands

- `rgd_geometry_demo`: populate the database with example shapefiles.
