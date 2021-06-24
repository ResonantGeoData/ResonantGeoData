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

COPY . /opt/rgd
# Use a directory name which will never be an import name, as isort considers this as first-party.
WORKDIR /opt/rgd
RUN pip install \
    --find-links https://girder.github.io/large_image_wheels \
    -e ./django-rgd[fuse] \
    -e ./testing-utils \
    -e ./example_project
RUN pip install \
    --find-links https://girder.github.io/large_image_wheels \
    -e ./django-rgd-3d[worker] \
    -e ./django-rgd-fmv[worker] \
    -e ./django-rgd-geometry[worker] \
    -e ./django-rgd-imagery[worker] \
    ipython \
    tox

ENTRYPOINT ["/opt/django-project-services/fuse.sh"]
