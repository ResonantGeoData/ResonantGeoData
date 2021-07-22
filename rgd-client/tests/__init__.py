import os

# python used to execute manage.py
PYTHON_PATH = os.environ.get('TEST_PYTHON_PATH', '/usr/local/bin/python')

# path to manage.py for example_project
MANAGE_PATH = os.path.normpath(os.path.join(os.getcwd(), './manage.py'))

# django settings module
SETTINGS_MODULE = os.environ.get('DJANGO_SETTINGS_MODULE', 'test_project.settings')
