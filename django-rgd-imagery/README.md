[![logo](https://raw.githubusercontent.com/ResonantGeoData/ResonantGeoData/main/logos/RGD_Logo.png)](https://github.com/ResonantGeoData/ResonantGeoData/)

# Resonant GeoData Imagery

[![PyPI](https://img.shields.io/pypi/v/django-rgd-imagery.svg?logo=python&logoColor=white)](https://pypi.org/project/django-rgd-imagery/)

A submodule of Resonant GeoData for storing imagery supporting annotations and spatial reference.


## Installation

Follow the instructions for the core `django-rgd` app first, then

```
pip install --find-links https://girder.github.io/large_image_wheels django-rgd-imagery
```

Add this app to your `INSTALLED_APPS` along with the core RGD app:

```py
INSTALLED_APPS += [
    'django.contrib.gis',
    'rgd',
    'rgd_imagery',
]
```

## Configurations

The RGD imagery submodule has an optional setting:

- `RGD_STAC_BROWSER_LIMIT`: (default of 1000) limit the response of STAC collection queries. An exception will be raised if a collection is requested with more than this many items.
- Use the `MEMCACHE_*` options from `django-rgd` to configure `large_image` for use with Memcached.

## Models

This app adds quite a few additional models on top of the core app for storing image data


## Management Commands

- `rgd_imagery_demo`: populate the database with example image data (image sets, annotations, rasters, etc.).
- `rgd_imagery_landsat_rgb_s3`: populate the database with example raster data of the RGB bands of Landsat 8 imagery hosted on a public S3 bucket.


## Notable Features

- STAC Item ingest/export for raster imagery
- Image tile serving through `large_image`
- Image annotation support
- KWCOCO image archive and annotation ingest
- Cloud Optimized GeoTIFF conversion utility
- Extract ROIs from imagery in pixel and world coordinates
