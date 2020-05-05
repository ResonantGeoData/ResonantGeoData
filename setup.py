from setuptools import setup

setup(
    name='socom-challenge',
    version='0.1',
    python_requires='>=3.6.0',
    install_requires=[
        'boto3',
        'celery',
        'dictdiffer',
        'django',
        'django-admin-display',
        'django-allauth',
        'django-cleanup',
        'django-cors-headers',
        'django-import-export',
        'django-markdownify',
        'django-s3-file-field',
        'django-storages',
        'django-unused-media',
        'djangorestframework',
        'docker',
        # 'isic-challenge-scoring',
        # 'psycopg2',
        'requests',
        'rules',
        'uritemplate',
        # Production-only
        # 'django-heroku',
        # 'gunicorn',
        # 'sentry_sdk',
        # Development-only
        'django-debug-toolbar',
        'django-extensions',
        # 'django-minio-storage',
    ],
)
