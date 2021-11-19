[![logo](https://raw.githubusercontent.com/ResonantGeoData/ResonantGeoData/main/logos/RGD_Logo.png)](https://github.com/ResonantGeoData/ResonantGeoData/)

# Resonant GeoData 3D

[![PyPI](https://img.shields.io/pypi/v/django-rgd-3d.svg?logo=python&logoColor=white)](https://pypi.org/project/django-rgd-3d/)

A subapplication of Resonant GeoData for storing 3D data with an optional
spatial reference.


## Installation

Follow the instructions for the core `django-rgd` app first, then

```
pip install --find-links https://girder.github.io/large_image_wheels django-rgd-3d
```

Add this app to your `INSTALLED_APPS` along with the core RGD app:

```py
INSTALLED_APPS += [
    'django.contrib.gis',
    'rgd',
    'rgd_3d',
]
```


## Models

This app adds a few additional models on top of the core app for storign 3D data

- `Mesh3D`: the base 3D data model for ingesting data. This will automatically convert many popular formats to the VTP format. A 3D viewer is included for previewing these data on the front-end.
- `Mesh3DSpatial`: A way to link a geospatial context with `Mesh3D`.


## Management Commands

- `rgd_3d_demo`: populate the database with example 3D data.
