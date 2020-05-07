# Bane's Notes

For when we come back to this down the road

## Running Locally

Some additional notes from Bane for running locally:

- Make sure Docker is running
- Make sure RabbitMQ is launched

Launch site in background then launch celery worker:

```bash
python manage.py runserver 0.0.0.0:8081 &
python -m celery worker --app socom.celery --loglevel info --without-heartbeat
```

## Perusing the Code

`socom` is the main site
`core` is an app to control the "challenge"/"task" interface


FYI use [this blog](https://medium.com/@yathomasi1/1-using-django-extensions-to-visualize-the-database-diagram-in-django-application-c5fa7e710e16) to see a graph of the relational database:

```
python manage.py graph_models core -o core_app.png
```
