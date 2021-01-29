#!/bin/sh
mkdir -p /tmp/rgd/https
modprobe fuse
python -m simple_httpfs /tmp/rgd/https
exec "$@"
