# This file must be sourced, not run
vars='
DJANGO_CONFIGURATION=DevelopmentConfiguration
DJANGO_DATABASE_URL=postgres://postgres:postgres@localhost:5432/rgd
DJANGO_CELERY_BROKER_URL=amqp://localhost:5672/
DJANGO_MINIO_STORAGE_ENDPOINT=localhost:9000
DJANGO_MINIO_STORAGE_ACCESS_KEY=djangoAccessKey
DJANGO_MINIO_STORAGE_SECRET_KEY=djangoSecretKey
DJANGO_STORAGE_BUCKET_NAME=resonantgeodata
'
for var in $vars; do export "${var}"; done
