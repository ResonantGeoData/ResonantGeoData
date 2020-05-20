#!/usr/bin/env python
import os
import sys

import configurations.importer


def main():
    os.environ['DJANGO_SETTINGS_MODULE'] = 'rgd.settings'
    # Production usage runs manage.py for tasks like collectstatic,
    # so DJANGO_CONFIGURATION should always be explicitly set in production
    os.environ.setdefault('DJANGO_CONFIGURATION', 'DevelopmentConfiguration')
    # No need for check_options, users should always set DJANGO_CONFIGURATION
    configurations.importer.install(check_options=False)

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            'available on your PYTHONPATH environment variable? Did you '
            'forget to activate a virtual environment?'
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
