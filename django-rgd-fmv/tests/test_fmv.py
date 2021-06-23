import os

import pytest
from rgd.models.mixins import Status
from rgd_fmv.models import FMVMeta

NO_KWIVER = os.environ.get('NO_KWIVER', False)


@pytest.mark.django_db(transaction=True)
def test_populate_fmv_entry_from_klv_file(fmv_klv_file):
    # Since we provide the KLV file and the factory provides a dummpy MP4 file,
    #   the ETL routine will skip over those parts and just generate the FMVMeta
    fmv_entry = FMVMeta.objects.filter(fmv_file=fmv_klv_file).first()
    assert fmv_entry.ground_frames is not None


@pytest.mark.skipif(NO_KWIVER, reason='User set NO_KWIVER')
@pytest.mark.django_db(transaction=True)
def test_full_fmv_etl(fmv_video_file):
    assert fmv_video_file.status == Status.SUCCEEDED, fmv_video_file.failure_reason
    fmv_entry = FMVMeta.objects.get(fmv_file=fmv_video_file)
    assert fmv_entry.ground_frames is not None
