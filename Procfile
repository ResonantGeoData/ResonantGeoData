release: ./manage.py migrate
web: gunicorn --bind 0.0.0.0:$PORT rgd.wsgi
worker: REMAP_SIGTERM=SIGQUIT celery --app rgd.celery worker --loglevel INFO --without-heartbeat
flower: flower --broker=$CLOUDAMQP_URL
