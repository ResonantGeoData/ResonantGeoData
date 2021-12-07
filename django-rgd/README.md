[![logo](https://raw.githubusercontent.com/ResonantGeoData/ResonantGeoData/main/logos/RGD_Logo.png)](https://github.com/ResonantGeoData/ResonantGeoData/)

# Resonant GeoData Core Application

[![PyPI](https://img.shields.io/pypi/v/django-rgd.svg?logo=python&logoColor=white)](https://pypi.org/project/django-rgd/)

The core Resonant GeoData (RGD) app containing file and permissions management
as well as spatial models. Each of the other RGD apps depend on the core
functionality built here.


## Installation

```
pip install --find-links https://girder.github.io/large_image_wheels django-rgd
```

It is necessary to use a postgis database with the RGD apps. To do so, set your
database ENGINE to `django.contrib.gis.db.backends.postgis`.

Add RGD to your `INSTALLED_APPS`:

```py
INSTALLED_APPS += [
    'django.contrib.gis',
    'rgd',
]

MIDDLEWARE += ('crum.CurrentRequestUserMiddleware',)

REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] += ('rest_framework.authentication.TokenAuthentication',)
```

(note that RGD requires [`django-crum`](https://django-crum.readthedocs.io/en/latest/) middleware.)

It is also necessary to configure GDAL in your project settings:

```py
try:
    import re

    import osgeo

    libsdir = os.path.join(os.path.dirname(os.path.dirname(osgeo._gdal.__file__)), 'GDAL.libs')
    libs = {re.split(r'-|\.', name)[0]: os.path.join(libsdir, name) for name in os.listdir(libsdir)}
    GDAL_LIBRARY_PATH = libs['libgdal']
    GEOS_LIBRARY_PATH = libs['libgeos_c']
except Exception:
    pass
```

## Configurations

The RGD core app has a few optional settings:

- `RGD_GLOBAL_READ_ACCESS`: option to give all users access to files that lack permissions (otherwise only admin users can access these files)
- `RGD_FILE_FIELD_PREFIX`: the path prefix when uploading files to the project's S3 storage.
- `RGD_AUTO_APPROVE_SIGN_UP`: automatically approve all user sign ups.
- `RGD_AUTO_COMPUTE_CHECKSUMS`: automatically compute checksums for all ChecksumFile records (default False)
- `RGD_TEMP_DIR`: A temporary directory for working files
- `RGD_TARGET_AVAILABLE_CACHE`: The target free space to remain for the cache in Gigabytes (default 2).
- `RGD_REST_CACHE_TIMEOUT`: the time in seconds for the REST views cache (for endpoints that are cached).
- `MEMCACHED_USERNAME`, `MEMCACHED_PASSWORD`, and `MEMCACHED_URL`: use if hosting a memcached server to set the `default` django cache.
- `RGD_SIGNED_URL_TTL`: The time in seconds for which URL signatures are valid (defaults to 24 hours).
- `RGD_SIGNED_URL_QUERY_PARAM`: The signature querystring variable name (defaults to `signature`).

## Models

- `ChecksumFile`: the central file storage model. Supports uploaded files, S3 URLs, and http URLS.
- `Collection` and `CollectionPermission`: for grouping files and controlling permission groups on those groups.
- `SpatialEntry`: the core model for indexing spatial metadata. This is intended to be inherited from but also provides a robust search filter.
- `SpatialAsset`: a simple spatial model for registering any collection of files with manually inputted spatial metadata.
- `WhitelistedEmail`: a model for pre-approving users for sign up.


The core RGD app is intended to be inherited from for developing domain-specific
geospatial models. For instance, we will demo the implementation of the simple
`SpatialAsset` model shipped in this app.

We can develop a new model on top of `django-rgd` through the inheritting the
core `SpatialEntry` model and using a few mixin classes from `django-rgd`. This
new model will represent a collection of files with some spatial reference.

```py
from django_extensions.db.models import TimeStampedModel
from rgd.models import ChecksumFile, SpatialEntry


class SpatialAsset(SpatialEntry, TimeStampedModel):
    """Any spatially referenced file set."""
    files = models.ManyToManyField(ChecksumFile, related_name='+')
```

Just like that, you now have a way to associate a set of files to any geospatial
location. To populate data in this model, first create `ChecksumFile` records,
then create a new `SpatialAsset` populating the fields defined from
`SpatialEntry`: `acquisition_date`, `footprint`, `outline`, and `instrumentation`.


## Management Commands

The core app has two management commands:

- `rgd_s3_files`: used to ingest `ChecksumFile`s from S3 or
Google Cloud storage.
- `whitelist_email`: pre-approve users for sign-up.

Use the `--help` option for more details.
