from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _


class ItemTypeChoices(models.TextChoices):
    FEATURE = 'F', _('FEATURE')


class Item(models.Model):
    pass
