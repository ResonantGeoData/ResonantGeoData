from rgd_testing_utils.settings import *  # noqa

INSTALLED_APPS += [  # noqa
    'rgd_fmv',
]

ROOT_URLCONF = 'test_project.urls'

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
