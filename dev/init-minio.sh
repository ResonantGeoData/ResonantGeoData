#!/bin/bash
set -e
echo "Initializing the Minio container and making it ready for Django use:"

# Recreate the "minio" container and run it in the background
docker-compose up --force-recreate --detach minio

echo -n "Waiting for Minio to start ..."
"$( dirname "${BASH_SOURCE[0]}" )/wait-for/wait-for" localhost:9000
# The port binds slightly before the service is ready for connections
sleep 5
echo " done"

# Use the MinIO Client (mc) tool to:
# * Connect to the running Minio server
# * Make a bucket
# * Add an ordinary user, for use by Django
# * Grant the user read-write access to the bucket
#
# Use "docker run -t" for color output
# Run "mc" once with no output to suppress confusing mc initialization
docker run --rm -t --network resonantgeodata_default --entrypoint /bin/sh minio/mc -c '
/usr/bin/mc > /dev/null \
&& /usr/bin/mc config host add minio http://minio:9000 minioAdminAccessKey minioAdminSecretKey \
&& /usr/bin/mc mb -ignore-existing minio/resonantgeodata \
&& /usr/bin/mc admin user add minio djangoAccessKey djangoSecretKey \
&& /usr/bin/mc admin policy set minio readwrite user=djangoAccessKey'
# TODO: The name of the Docker Compose network is defined by the name of the parent directory
# TODO: Make the bucket name a parameter, so this script is reusable

docker-compose stop minio
