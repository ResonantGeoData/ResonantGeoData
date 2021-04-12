# `manage.py` Commands

There are several management commands to autpopulate the database with records.
Some of these commands pull and ingest data from `data.kitware.com` and others
catalog data that live on AWS S3 and Google Cloud Storage.

This document provide a list of all of these commands and some examples of how
to use them to populate the database.

Overall notes:

- These commands mostly need to run in the `celery` docker image unless otherwise noted.


## Standard Demo Data from DKC

There are two standard demo data commands to create records of sample data hosted
on `data.kitware.com` (DKC): `demo_data` and `wasabi`. The `demo_data` command will
pull data from DKC and create DB records while the `wasabi` command will point
to public facing URLs of Full Motion Video datasets on DKC rather than directly
downloading these large files.

Standard demo data for testing:
- Run `docker-compose run --rm celery ./manage.py demo_data`
- Run `docker-compose run --rm celery ./manage.py wasabi`

The `wasabi` data command can take a particularly long time to run as it is
processing large, remote video files.


## Auto Ingest Landsat and Sentinel Imagery

Cloud hosted satellite imagery:
- Google Cloud hosted Landsat and Sentinel imagery:
  - Landsat: `docker-compose run --rm celery ./manage.py gc_catalog landsat`
  - Sentinel: `docker-compose run --rm celery ./manage.py gc_catalog sentinel`
- S3 Hosted imagery (soon to go offline by June 2021)
  - Run `docker-compose run --rm celery ./manage.py s3_landsat`

For the `gc_catalog` and `s3_landsat` commands, the `-c` argument is optional and
allows you to control how much imagery to ingest; the full dataset can
take a long time to ingest. These routines actually use a subset of the full
catalogs hosted on data.kitware.com; [@banesullivan](https://github.com/banesullivan)
has local scripts to create the subsets of these catalogs.


## Auto Ingest File Records from Cloud Storage

The `ingest_s3` command is for automatically ingesting `ChecksumFile` records
for any remote, cloud hosted files on AWS S3 or Google Cloud Storage.

This command simply creates file entries and requires the user to make their
own script to create raster, geometry, or FMV records of these files.

Here are some examples on how to ingest files automatically from Google Cloud Storage:

- `docker-compose run --rm django ingest_s3 gcp-public-data-landsat --prefix LC08/01/044/076/LC08_L1GT_044076_20161001_20170320_01_T2 --google --exclude-regex=\$\w+\$`

Since this command is only creating `ChecksumFile` records and we have that
model's associated tasks to only run on demand, this command can run in the
lighter `django` image.
