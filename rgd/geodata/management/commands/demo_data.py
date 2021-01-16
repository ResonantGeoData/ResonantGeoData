from functools import reduce
import os

from django.conf import settings
from django.core.management.base import BaseCommand  # , CommandError
from django.db.models import Count

from rgd.geodata import models
from rgd.geodata.datastore import datastore, registry
from rgd.utility import compute_checksum, get_or_create_no_commit

SUCCESS_MSG = 'Finished loading all demo data.'

# Names of files in the datastore
IMAGE_FILES = []
RASTER_FILES = [
    '20091021202517-01000100-VIS_0001.ntf',
    'aerial_rgba_000003.tiff',
    'cclc_schu_100.tif',
    'landcover_sample_2000.tif',
    'paris_france_10.tiff',
    'rgb_geotiff.tiff',
    'RomanColosseum_WV2mulitband_10.tif',
    [
        'LC08_L1TP_034032_20200429_20200509_01_T1_sr_band1.tif',
        'LC08_L1TP_034032_20200429_20200509_01_T1_sr_band2.tif',
        'LC08_L1TP_034032_20200429_20200509_01_T1_sr_band3.tif',
    ],
    'Elevation.tif',
    'L1C_T13SCD_A019901_20201227T175922.tif',
    'L1C_T18TWN_A016525_20200505T155731.tif',
    'L1C_T18TWN_A018527_20200922T155115.tif',
    'L1C_T18TWN_A025648_20200520T155359.tif',
    'L1C_T18TWN_A027793_20201017T155552.tif',
    'L1C_T18TWN_A028079_20201106T160014.tif',
    # 'bpasg_emodis_week34_082320.tif',
    # 'vegdri_diff_2020_34_gtif.tif',
    # 'vegdri_emodis_week34_082320.tif',
    # 'US_eMAH_NDVI.2020.350-356.1KM.VI_ACQI.006.2020359165956.tif',
    # 'US_eMAH_NDVI.2020.350-356.1KM.VI_NDVI.006.2020359165956.tif',
    # 'US_eMAH_NDVI.2020.350-356.1KM.VI_QUAL.006.2020359165956.tif',
    'TC_NG_SFBay_US_Geo.tif',
]
SHAPE_FILES = [
    'Streams.zip',
    'Watershedt.zip',
    'MuniBounds.zip',
    'lm_cnty.zip',
    'dlwatersan.zip',
    'dlschool.zip',
    'dlpark.zip',
    'dlmetro.zip',
    'dllibrary.zip',
    'dlhospital.zip',
    'dlfire.zip',
    'Solid_Mineral_lease_1.zip',
    'AG_lease.zip',
]
FMV_FILES = []
KWCOCO_ARCHIVES = [['demo.kwcoco.json', 'demodata.zip'], ['demo_rle.kwcoco.json', 'demo_rle.zip']]


def _get_or_create_file_model(model, name):
    def download_and_create():
        # Create the ImageFile entry
        path = datastore.fetch(name)
        entry = model()
        entry.name = name
        entry.file.save(os.path.basename(path), open(path, 'rb'))
        return entry

    # Check if there is already an image file with this name
    #  to avoid duplicating data (and check sha512)
    sha = registry[name].split(':')[1]  # NOTE: assumes sha512
    q = model.objects.filter(name=name)
    entry = None
    for entry in q:
        if compute_checksum(entry.file, sha512=True) == sha:
            break
    if entry is None:
        entry = download_and_create()
    return entry


class Command(BaseCommand):
    help = 'Populate database with demo data.'

    def _load_image_files(self, images):
        ids = []
        for imfile in images:
            if isinstance(imfile, (list, tuple)):
                result = self._load_image_files(imfile)
            else:
                entry = _get_or_create_file_model(models.ImageFile, imfile)
                result = entry.imageentry.pk
            ids.append(result)
        return ids

    def _load_raster_files(self):
        imentries = self._load_image_files(RASTER_FILES)
        ids = []
        for pks in imentries:
            if not isinstance(pks, (list, tuple)):
                pks = [
                    pks,
                ]
            # Check if an ImageSet already exists containing all of these images
            q = models.ImageSet.objects.annotate(count=Count('images')).filter(count=len(pks))
            imsets = reduce(lambda p, id: q.filter(images=id), pks, q).values()
            if len(imsets) > 0:
                # Grab first, could be N-many
                imset = models.ImageSet.objects.get(id=imsets[0]['id'])
            else:
                images = models.ImageEntry.objects.filter(pk__in=pks).all()
                imset = models.ImageSet()
                imset.save()  # Have to save before adding to ManyToManyField
                for image in images:
                    imset.images.add(image)
                imset.save()
            # Make raster of that image set
            raster, _ = models.RasterEntry.objects.get_or_create(image_set=imset)
            ids.append(raster.pk)
        return ids

    def _load_shape_files(self):
        ids = []
        for shpfile in SHAPE_FILES:
            entry = _get_or_create_file_model(models.GeometryArchive, shpfile)
            ids.append(entry.geometryentry.pk)
        return ids

    def _load_fmv_files(self):
        raise NotImplementedError('FMV ETL with Docker is still broken.')

    def _load_kwcoco_archives(self):
        ids = []
        for fspec, farch in KWCOCO_ARCHIVES:
            spec = _get_or_create_file_model(models.ArbitraryFile, fspec)
            arch = _get_or_create_file_model(models.ArbitraryFile, farch)
            ds, _ = get_or_create_no_commit(
                models.KWCOCOArchive, spec_file=spec, image_archive=arch
            )
            ds.save()
            ids.append(ds.id)
        return ids

    def handle(self, *args, **options):
        # Set celery to run all tasks synchronously
        eager = getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False)
        prop = getattr(settings, 'CELERY_TASK_EAGER_PROPAGATES', False)
        settings.CELERY_TASK_ALWAYS_EAGER = True
        settings.CELERY_TASK_EAGER_PROPAGATES = True

        # Run the command
        self._load_image_files(IMAGE_FILES)
        self._load_raster_files()
        self._load_shape_files()
        # self._load_fmv_files()
        self._load_kwcoco_archives()
        self.stdout.write(self.style.SUCCESS(SUCCESS_MSG))

        # Reset celery to previous settings
        settings.CELERY_TASK_ALWAYS_EAGER = eager
        settings.CELERY_TASK_EAGER_PROPAGATES = prop
