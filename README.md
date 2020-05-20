# ResonantGeoData
2D/3D/4D Geospatial Data API and Machine Learning System for Evaluation

## Develop with Docker (recommended)

This is the simplest configuration for developers to start with.
### Initial Setup
1. Run `./dev/init-minio.sh`
2. Run `docker-compose run web ./manage.py migrate`
3. Run `docker-compose run web ./manage.py createsuperuser` and follow the prompts to create your own user

### Run Application
1. Run `docker-compose up`
2. When finished, use `Ctrl+C`

## Develop natively (advanced)
This configuration still uses Docker to run attached services in the background,
but allows developers to run the Python code on their native system.

### Initial Setup
1. Run `./dev/init-minio.sh`
2. Run `docker-compose -f ./docker-compose.yml up -d`
3. Install Python 3.8
4. Install [`psycopg2` build prerequisites](https://www.psycopg.org/docs/install.html#build-prerequisites)
5. Create and activate a new Python virtualenv
6. Run `pip install -e .`
7. Run `source ./dev/.env-docker-compose-native.sh`
8. Run `./manage.py migrate`
9. Run `./manage.py createsuperuser` and follow the prompts to create your own user

### Run Application
1. Run (in separate windows) both:
   1. `./manage.py runserver`
   2. `celery worker --app rgd.celery --loglevel info --without-heartbeat`
2.  When finished, run `docker-compose stop`

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
