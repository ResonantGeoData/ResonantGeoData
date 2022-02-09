FROM condaforge/miniforge3
LABEL "repository"="https://github.com/ResonantGeoData/ResonantGeoData"
LABEL "maintainer"="Kitware, Inc. <rgd@kitware.com>"

###############################################################################
#### Install ALL dependencies are managed by environment.yml
COPY environment.yml /opt/django-project/
RUN conda env update --name base --file /opt/django-project/environment.yml

###############################################################################
#### Install and configure development project
# Only copy the setup.py, it will still force all install_requires to be installed,
# but find_packages() will find nothing (which is fine). When Docker Compose mounts the real source
# over top of this directory, the .egg-link in site-packages resolves to the mounted directory
# and all package modules are importable.
COPY ./version.py /opt/django-project/
COPY ./django-rgd/setup.py /opt/django-project/django-rgd/
COPY ./django-rgd-3d/setup.py /opt/django-project/django-rgd-3d/
COPY ./django-rgd-fmv/setup.py /opt/django-project/django-rgd-fmv/
COPY ./django-rgd-geometry/setup.py /opt/django-project/django-rgd-geometry/
COPY ./django-rgd-imagery/setup.py /opt/django-project/django-rgd-imagery/
COPY ./example_project/setup.py /opt/django-project/example_project/
# Use a directory name which will never be an import name, as isort considers this as first-party.
# Use `--no-deps` since all dependencies are managed by conda
WORKDIR /opt/django-project
RUN pip install \
    --no-deps \
    -e ./django-rgd \
    -e ./django-rgd-3d \
    -e ./django-rgd-fmv \
    -e ./django-rgd-geometry \
    -e ./django-rgd-imagery \
    -e ./example_project

WORKDIR /opt/django-project/
