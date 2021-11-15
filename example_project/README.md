# Example Project

For better performance during demos, run:

```
$ docker compose run --rm django ./example_project/manage.py collectstatic

$ docker compose -f docker-compose.yml -f docker-compose.override.yml -f docker-compose.demo.yml up
```
