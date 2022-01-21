# Example Project

For better performance during demos, run:

```
$ docker compose run --rm django ./example_project/manage.py collectstatic

$ docker compose -f docker-compose.yml -f docker-compose.override.yml -f docker-compose.demo.yml up
```

For using the miniforge environment (useful on M1 Mac):

```
$ docker compose -f docker-compose.yml -f docker-compose.override.yml -f docker-compose.override.miniforge.yml up
```
