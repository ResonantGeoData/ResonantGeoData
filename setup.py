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
        'django-storages',
        'djangorestframework',
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
        'gunicorn',
        # Development-only
        'django-debug-toolbar',
        'django-minio-storage',
    ],
)
