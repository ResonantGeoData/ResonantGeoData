[![logo](https://raw.githubusercontent.com/ResonantGeoData/ResonantGeoData/main/logos/RGD_Logo.png)](https://github.com/ResonantGeoData/ResonantGeoData/)

# Resonant GeoData 3D

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

- `PointCloud`: the base 3D data model for ingesting data. This will convert many popular formats to the VTP format and automatically produce a `PointCloudMeta` record.
- `PointCloudMeta`: the model containing the 3D data. This is either automatically generated or manually geerated by uploaded 3D data in the VTP format. A 3D viewer is included for previewing these data on the front-end.
- `PointCloudSpatial`: A way to link a geospatial context with `PointCloudMeta`.


## Management Commands

- `rgd_3d_demo`: populate the database with example 3D data.
