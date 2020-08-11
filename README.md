# ResonantGeoData

[![codecov](https://codecov.io/gh/ResonantGeoData/ResonantGeoData/branch/master/graph/badge.svg)](https://codecov.io/gh/ResonantGeoData/ResonantGeoData)

2D/3D/4D Geospatial Data API and Machine Learning System for Evaluation

## Develop with Docker (recommended)

This is the simplest configuration for developers to start with.
### Initial Setup
1. Run `docker-compose run --rm django ./manage.py migrate`
2. Run `docker-compose run --rm django ./manage.py createsuperuser`
   and follow the prompts to create your own user

### Run Application
1. Run `docker-compose up`
2. Access the site, starting at http://localhost:8000/admin/
3. When finished, use `Ctrl+C`

On Mac, be sure to set:

```bash
export DOCKER_SOCK=/var/run/docker.sock
export DOCKER_CMD=/usr/local/bin/docker
```

### Application Maintenance
Occasionally, new package dependencies or schema changes will necessitate
maintenance. To non-destructively update your development stack at any time:
1. Run `docker-compose pull`
2. Run `docker-compose build`
3. Run `docker-compose run --rm django ./manage.py migrate`

## Develop Natively (advanced)
This configuration still uses Docker to run attached services in the background,
but allows developers to run the Python code on their native system.

### Initial Setup
1. Run `docker-compose -f ./docker-compose.yml up -d`
2. Install Python 3.8
3. Install
   [`psycopg2` build prerequisites](https://www.psycopg.org/docs/install.html#build-prerequisites)
4. Create and activate a new Python virtualenv
5. Run `pip install -e .`
6. Run `source ./dev/source-native-env.sh`
7. Run `./manage.py migrate`
8. Run `./manage.py createsuperuser` and follow the prompts to create your own user

### Run Application
1. Run (in separate windows) both:
   1. `./manage.py runserver`
   2. `celery worker --app {{ cookiecutter.pkg_name }}.celery --loglevel info --without-heartbeat`
2. When finished, run `docker-compose stop`

## Remap Service Ports (optional)
Attached services may be exposed to the host system via alternative ports. Developers who work
on multiple software projects concurrently may find this helpful to avoid port conflicts.

To do so, before running any `docker-compose` commands, set any of the environment variables:
* `DOCKER_POSTGRES_PORT`
* `DOCKER_RABBITMQ_PORT`
* `DOCKER_MINIO_PORT`

The Django server must be informed about the changes:
* When running the "Develop with Docker" configuration, override the environment variables:
  * `DJANGO_MINIO_STORAGE_MEDIA_URL`, using the port from `DOCKER_MINIO_PORT`.
* When running the "Develop Natively" configuration, override the environment variables:
  * `DJANGO_DATABASE_URL`, using the port from `DOCKER_POSTGRES_PORT`
  * `DJANGO_CELERY_BROKER_URL`, using the port from `DOCKER_RABBITMQ_PORT`
  * `DJANGO_MINIO_STORAGE_ENDPOINT`, using the port from `DOCKER_MINIO_PORT`

Since most of Django's environment variables contain additional content, use the values from
the appropriate `dev/.env.docker-compose*` file as a baseline for overrides.

## Testing
### Initial Setup
Tox is required to execute all tests.
It may be installed with `pip install tox`.

### Running tests
Run `tox` to launch the full test suite.

Individual test environments may be selectively run.
This also allows additional options to be be added.
Useful sub-commands include:
* `tox -e lint`: Run only the style checks.
* `tox -e type`: Run only the type checks.
* `tox -e py3`: Run only the unit tests.

To automatically reformat all code to comply with
some (but not all) of the style checks, run `tox -e format`.

## Sample Algorithms

There are a few sample algorithms on <https://data.kitware.com> in the ResonantGeoData collection.
