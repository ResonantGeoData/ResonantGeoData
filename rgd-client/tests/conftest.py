import os
import signal
import subprocess
import time

import requests

from . import MANAGE_PATH, PYTHON_PATH, SETTINGS_MODULE
from .data_fixtures import generate_fixtures, sources

proc = None
max_attempts = 10  # number of attempts to connect to server
timeout = 5  # time in seconds between connection attempts


# setup before all tests
def pytest_configure(config):
    global proc

    for (name, fixture) in generate_fixtures():
        globals()[name] = fixture

    # reset db
    subprocess.run(
        [PYTHON_PATH, MANAGE_PATH, 'reset_db', '--noinput'],
        env={'DJANGO_SETTINGS_MODULE': SETTINGS_MODULE},
    )

    # run migrations
    subprocess.run(
        [PYTHON_PATH, MANAGE_PATH, 'migrate'],
        env={'DJANGO_SETTINGS_MODULE': SETTINGS_MODULE},
    )

    # create user for client
    # TODO: use better fields
    subprocess.run(
        [PYTHON_PATH, MANAGE_PATH, 'createsuperuser', '--no-input'],
        env={
            'DJANGO_SUPERUSER_USERNAME': 'test',
            'DJANGO_SUPERUSER_EMAIL': 'test@kitware.com',
            'DJANGO_SUPERUSER_PASSWORD': 'testing',
        },
    )

    # start server as background process
    proc = subprocess.Popen(
        [PYTHON_PATH, MANAGE_PATH, 'runserver', '0.0.0.0:8000'],
        env={
            'DJANGO_SETTINGS_MODULE': SETTINGS_MODULE,
        },
        preexec_fn=os.setsid,
    )

    # sleep and poll until server is ready
    ready = False
    attempts = 0
    while (not ready) and attempts < max_attempts:
        try:
            resp = requests.get('http://localhost:8000')
            if resp.status_code == 200:
                ready = True
        except requests.exceptions.ConnectionError:
            attempts += 1
            time.sleep(timeout)

    if not ready:
        raise Exception('Could not connect to server')


# teardown after all tests
def pytest_unconfigure(config):
    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)

    for s in sources:
        config.cache.set(s, False)
