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
        && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Only copy the setup.py, it will still force all install_requires to be installed,
# but find_packages() will find nothing (which is fine). When Docker Compose mounts the real source
# over top of this directory, the .egg-link in site-packages resolves to the mounted directory
# and all package modules are importable.
COPY ./setup.py /opt/django/setup.py
WORKDIR /opt/django
RUN pip install \
    --find-links https://girder.github.io/large_image_wheels \
    GDAL \
    -e .[dev,worker]
