import os
import signal
import subprocess
import time

import requests

proc = None
python_path = '/usr/local/bin/python'
max_attempts = 10  # number of attempts to connect to server
timeout = 5  # time in seconds between connection attempts


# setup before all tests
def pytest_configure(config):
    global proc

    # path to manage.py for example_project
    manage_path = os.path.normpath(os.path.join(os.getcwd(), '../../example_project/manage.py'))

    # run migrations
    subprocess.run(
        [python_path, manage_path, 'migrate'],
        env={"DJANGO_SETTINGS_MODULE": "rgd_example.settings"},
    )

    # start server as background process
    proc = subprocess.Popen(
        [python_path, manage_path, 'runserver', '0.0.0.0:8000'],
        env={"DJANGO_SETTINGS_MODULE": "rgd_example.settings"},
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
