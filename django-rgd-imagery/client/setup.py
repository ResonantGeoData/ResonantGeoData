from io import open as io_open
import os
from pathlib import Path

from setuptools import find_packages, setup

base_dir = Path(__file__).parent
readme_file = base_dir / 'README.md'
if readme_file.exists():
    with readme_file.open() as f:
        long_description = f.read()
else:
    # When this is first installed in development Docker, README.md is not available
    long_description = ''

__version__ = None
filepath = os.path.dirname(__file__)
version_file = os.path.join(filepath, '..', '..', 'version.py')
with io_open(version_file, mode='r') as fd:
    exec(fd.read())

setup(
    name='rgd-imagery-client',
    version=__version__,
    description='Make web requests to a Resonant GeoData instance.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='Apache 2.0',
    author='Kitware, Inc.',
    author_email='rgd@kitware.com',
    url='https://github.com/ResonantGeoData/ResonantGeoData',
    keywords='',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python',
    ],
    python_requires='>=3.8',
    packages=find_packages(exclude=['tests']),
    install_requires=['rgd_client'],
    extras_require={'dev': ['ipython'], 'widgets': ['ipyleaflet']},
    entry_points={'rgd_client.plugin': ['rgd_imagery_client = rgd_imagery_client:ImageryClient']},
)
