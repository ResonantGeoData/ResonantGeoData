from setuptools import setup

setup(
    name='resonantgeodata',
    version='0.1',
    python_requires='>=3.8.0',
    install_requires=[
        'boto3',
        'celery!=4.4.4',
        'django',
        'django-admin-display',
        'django-allauth',
        'django-cleanup',
        'django-configurations[database]',
        'django-cors-headers',
        'django-crispy-forms',
        'django-extensions',
        'django-filter',
        'django-s3-file-field',
        'django-storages',
        'djangorestframework',
        'djproxy',
        'docker',
        'drf-yasg',
        'gputil',
        'psycopg2',
        'python-magic',
        'rules',
        'uritemplate',
        'whitenoise[brotli]',
        # Production-only
        'django-storages',
        'flower',
        'gunicorn',
        # Development-only
        'django-debug-toolbar',
        'django-minio-storage',
        # GeoData
        'rasterio',
        'fiona',
        'shapely',
    ],
)
