#!/bin/sh
mkdir -p /tmp/rgd/https
python -m simple_httpfs /tmp/rgd/https
mkdir -p /tmp/rgd/http
python -m simple_httpfs /tmp/rgd/http
exec "$@"
