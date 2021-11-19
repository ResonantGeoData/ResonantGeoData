from rgd.management.commands._data_helper import _get_or_create_file_model
from rgd_fmv import models


def load_fmv_files(fmv_files):
    return [_get_or_create_file_model(models.FMV, fmv).id for fmv in fmv_files]
