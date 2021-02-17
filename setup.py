from pathlib import Path

from setuptools import find_packages, setup

readme_file = Path(__file__).parent / 'README.md'
if readme_file.exists():
    with readme_file.open() as f:
        long_description = f.read()
else:
    # When this is first installed in development Docker, README.md is not available
    long_description = ''

setup(
    name='resonantgeodata',
    version='0.1.0',
    description='',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='Apache 2.0',
    author='Kitware, Inc.',
    author_email='kitware@kitware.com',
    keywords='',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django :: 3.0',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python',
    ],
    python_requires='>=3.8',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'celery',
        'django==3.2a1',
        'django-admin-display',
        'django-allauth',
        'django-cleanup',
        'django-configurations[database,email]',
        'django-crispy-forms',
        'django-extensions',
        'django-filter',
        'django-girder-utils',
        'django-model-utils',
        'django-oauth-toolkit',
        'djangorestframework',
        'docker',
        'drf-yasg',
        'GDAL',
        'numpy',
        'Pillow',
        'pooch',
        'python-magic',
        'rules',
        'uritemplate',
        # Production-only
        'django-composed-configuration[prod]',
        'django-s3-file-field[minio]',
        'flower',
        'gunicorn',
    ],
    extras_require={
        'dev': [
            'django-composed-configuration[dev]',
            'django-debug-toolbar',
            'django-s3-file-field[minio]',
            'ipython',
            'tox',
        ],
        'worker': [
            'rasterio',
            'fiona',
            'shapely',
            'scipy',
            'kwarray>=0.5.10',
            'kwcoco',
            'kwimage>=0.6.7',
        ],
    },
)
