from django.contrib.postgres.operations import CreateExtension
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0015_algorithmresult_data_mimetype'),
    ]

    operations = [
        CreateExtension('postgis'),
    ]
