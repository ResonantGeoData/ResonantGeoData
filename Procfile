release: ./manage.py migrate
web: gunicorn --bind 0.0.0.0:$PORT rgd.wsgi
worker: REMAP_SIGTERM=SIGQUIT celery worker --app rgd.celery --loglevel info --without-heartbeat
