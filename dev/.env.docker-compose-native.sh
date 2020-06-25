# This file must be sourced, not run

export DJANGO_CONFIGURATION=DevelopmentConfiguration
export DJANGO_DATABASE_URL="postgres://postgres:postgres@localhost:5432/rgd"
export DJANGO_CELERY_BROKER_URL="amqp://localhost:5672/"
export DJANGO_MINIO_STORAGE_ENDPOINT=localhost:9000
export DJANGO_MINIO_STORAGE_ACCESS_KEY=djangoAccessKey
export DJANGO_MINIO_STORAGE_SECRET_KEY=djangoSecretKey
export DJANGO_STORAGE_BUCKET_NAME=resonantgeodata
