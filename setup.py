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
    version='0.1.1',
    description='',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='Apache 2.0',
    author='Kitware, Inc.',
    author_email='kitware@kitware.com',
    url='https://github.com/ResonantGeoData/ResonantGeoData',
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
        'boto3',
        'celery',
        'django>=3.2',  # See PR #264: due to this bug: https://code.djangoproject.com/ticket/31910
        'django-allauth',
        'django-cleanup',
        'django-click',
        'django-configurations[database,email]',
        'django-crispy-forms',
        'django-extensions',
        'django-filter',
        'django-girder-utils',
        'django-model-utils',
        'django-oauth-toolkit',
        'djangorestframework',
        'drf-yasg',
        'GDAL',
        'large-image>=1.6.0',
        'large-image-source-gdal',
        'large-image-source-pil',
        'numpy',
        'pooch',
        'python-magic',
        'pystac[validation]',
        'rules',
        'uritemplate',
        # Production-only
        'django-composed-configuration[prod]>=0.16',
        'django-s3-file-field[minio]',
        'flower',
        'gunicorn',
    ],
    extras_require={
        'dev': [
            'django-composed-configuration[dev]>=0.16',
            'django-debug-toolbar',
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
            'kwimage[headless]>=0.6.7',
            'large-image-converter',
            'pyntcloud[LAS]',
            'pyvista',
        ],
        'fuse': [
            'simple-httpfs',
        ],
        'fmv': [
            'kwiver',
        ],
    },
)
