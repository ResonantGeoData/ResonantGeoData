from rgd_testing_utils.settings import *  # noqa


INSTALLED_APPS += [  # noqa
    'rgd_3d',
    'rgd_fmv',
    'rgd_geometry',
    'rgd_imagery',
]

ROOT_URLCONF = 'rgd_example.urls'
WSGI_APPLICATION = 'rgd_example.wsgi.application'
