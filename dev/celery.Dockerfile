FROM python:3.8-slim
# Install system librarires for Python packages:
# * psycopg2
# * python-magic
RUN apt-get update && \
    apt-get install --no-install-recommends --yes \
        libpq-dev \
        gcc \
        libc6-dev \
        libmagic1 \
        libgl1-mesa-glx \
        libglib2.0-0 \
        ffmpeg \
        fuse \
        && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY ./dev/fuse.sh /opt/django-project-services/fuse.sh

# Only copy the setup.py, it will still force all install_requires to be installed,
# but find_packages() will find nothing (which is fine). When Docker Compose mounts the real source
# over top of this directory, the .egg-link in site-packages resolves to the mounted directory
# and all package modules are importable.
COPY ./django-rgd/setup.py /opt/django-project/django-rgd/
COPY ./django-rgd-3d/setup.py /opt/django-project/django-rgd-3d/
COPY ./django-rgd-fmv/setup.py /opt/django-project/django-rgd-fmv/
COPY ./django-rgd-geometry/setup.py /opt/django-project/django-rgd-geometry/
COPY ./django-rgd-imagery/setup.py /opt/django-project/django-rgd-imagery/
COPY ./example_project/setup.py /opt/django-project/example_project/
# Use a directory name which will never be an import name, as isort considers this as first-party.
WORKDIR /opt/django-project
RUN pip install \
    --find-links https://girder.github.io/large_image_wheels \
    -e ./django-rgd[fuse] \
    -e ./example_project
RUN pip install \
    --find-links https://girder.github.io/large_image_wheels \
    -e ./django-rgd-3d[worker] \
    -e ./django-rgd-fmv[worker] \
    -e ./django-rgd-geometry[worker] \
    -e ./django-rgd-imagery[worker] \
    ipython \
    tox

WORKDIR /opt/django-project/
ENTRYPOINT ["/opt/django-project-services/fuse.sh"]
