from io import StringIO

from django.core.management import call_command


def _call_command(name, *args, **kwargs):
    out = StringIO()
    call_command(
        name,
        *args,
        stdout=out,
        stderr=StringIO(),
        **kwargs,
    )
    return out.getvalue()
