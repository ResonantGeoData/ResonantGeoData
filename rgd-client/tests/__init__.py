import os

# python used to execute manage.py
PYTHON_PATH = os.environ.get('TEST_PYTHON_PATH', '/usr/local/bin/python')

# path to manage.py for example_project
MANAGE_PATH = os.path.normpath(os.path.join(os.getcwd(), '../../example_project/manage.py'))
