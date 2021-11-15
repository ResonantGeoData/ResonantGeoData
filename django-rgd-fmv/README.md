[![logo](https://raw.githubusercontent.com/ResonantGeoData/ResonantGeoData/main/logos/RGD_Logo.png)](https://github.com/ResonantGeoData/ResonantGeoData/)

# Resonant GeoData Full Motion Video (FMV)

[![PyPI](https://img.shields.io/pypi/v/django-rgd-fmv.svg?logo=python&logoColor=white)](https://pypi.org/project/django-rgd-fmv/)

A submodule of Resonant GeoData for storing Full Motion Video (FMV) datasets


## Installation

Follow the instructions for the core `django-rgd` app first, then

```
pip install --find-links https://girder.github.io/large_image_wheels django-rgd-fmv
```

Add this app to your `INSTALLED_APPS` along with the core RGD app:

```py
INSTALLED_APPS += [
    'django.contrib.gis',
    'rgd',
    'rgd_fmv',
]
```


## Models

This app adds a few additional models on top of the core app for storing FMV data

- `FMV`: the base data model for ingesting FMV data. This will preprocess the video file using KWIVER to generate a `FMVMeta` record with the spatial metadata extracted.
- `FMVMeta`: an automatically populated record of the data extracted from the FMV data with spatial context.

## Management Commands

- `rgd_fmv_demo`: populate the database with example FMV data.
- `rgd_fmv_wasabi`: populate the database with example FMV data from the WASABI project.
