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
        && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /opt/resonantgeodata/requirements.txt
RUN pip install -r /opt/resonantgeodata/requirements.txt

COPY ./setup.py /opt/resonantgeodata/setup.py
RUN pip install --editable /opt/resonantgeodata

WORKDIR /opt/resonantgeodata
