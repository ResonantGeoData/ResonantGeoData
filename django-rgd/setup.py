from pathlib import Path

from setuptools import find_packages, setup

readme_file = Path(__file__).parent.parent / 'README.md'
if readme_file.exists():
    with readme_file.open() as f:
        long_description = f.read()
else:
    # When this is first installed in development Docker, README.md is not available
    long_description = ''

setup(
    name='django-rgd',
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
    dependency_links=[
        'https://girder.github.io/large_image_wheels',
    ],
    install_requires=[
        'boto3',
        'celery',
        'django>=3.2',  # See PR #264: due to this bug: https://code.djangoproject.com/ticket/31910
        'django-allauth',
        'django-click',
        'django-filter',
        'django-girder-utils',
        'django-model-utils',
        'django-oauth-toolkit',
        'djangorestframework',
        'drf-yasg',
        'GDAL',
        'pooch',
        'psycopg2',
        'python-magic',
        'flower',
        # Production-only
        'django-s3-file-field[minio]',
    ],
    extras_require={
        'fuse': [
            'numpy',  # requirement of `simple-httpfs`
            'simple-httpfs',
        ],
    },
)