import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socom.settings.production')

app = Celery('socom', config_source='django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
