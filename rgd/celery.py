import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rgd.settings.development')

app = Celery('rgd', config_source='django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
