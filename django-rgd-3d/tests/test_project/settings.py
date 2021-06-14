from rgd_testing_utils.settings import *  # noqa


INSTALLED_APPS += [  # noqa
    'rgd_3d',
]

ROOT_URLCONF = 'test_project.urls'
WSGI_APPLICATION = 'test_project.wsgi.application'

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
