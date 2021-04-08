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

# Load version
with open(base_dir / 'rgdc' / 'version.py') as version_file:
    version = version_file.read().replace('__version__ = ', '').replace("'", '').strip()

setup(
    name='rgdc',
    version=version,
    description='Make web requests to a ResonantGeoData instance.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='Apache 2.0',
    author='Kitware, Inc.',
    author_email='kitware@kitware.com',
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
    install_requires=[
        'requests',
        'requests-toolbelt',
        'geomet',
    ],
    extras_require={'dev': ['ipython']},
)
