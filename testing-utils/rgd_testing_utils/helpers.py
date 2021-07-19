from django.core.exceptions import FieldDoesNotExist
from django.db.models import ForeignKey, ManyToManyField, OneToOneField
import pytest
from rgd import models
from rgd.permissions import get_collection_permissions_paths


def check_model_permissions(model):
    if not issubclass(model, models.mixins.PermissionPathMixin):
        return

    try:
        permissions_paths = get_collection_permissions_paths(model)
        assert permissions_paths  # field exists and non-empty
    except TypeError:
        pytest.fail('permissions_paths does not exist on model')

    # iterate paths
    for path in permissions_paths:
        fields = path.split('__')
        current_model = model

        # iterate fields which span relations
        for f in fields:

            # reached end of lookup path
            if f == '':
                return

            # check that relation exists on current model
            try:
                if (
                    isinstance(current_model, ForeignKey)
                    or isinstance(current_model, ManyToManyField)
                    or isinstance(current_model, OneToOneField)
                ):
                    current_model = current_model.related_model

                current_model = current_model._meta.get_field(f)
            except FieldDoesNotExist:
                pytest.fail(
                    'Path error: field {} does not exist on model {}'.format(
                        f, current_model.__str__
                    )
                )
