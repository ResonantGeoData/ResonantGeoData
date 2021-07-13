from django.apps import apps
from rgd_testing_utils.helpers import check_model_permissions


def test_check_permissions_path_rgd_fmv():
    for model in apps.get_app_config('rgd_fmv').get_models():
        check_model_permissions(model)
