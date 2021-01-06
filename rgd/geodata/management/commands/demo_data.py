import os

from django.conf import settings
from django.core.management.base import BaseCommand  # , CommandError

from rgd.geodata import models
from rgd.geodata.datastore import datastore

# Run all tasks synchronously
settings.CELERY_TASK_ALWAYS_EAGER = True
settings.CELERY_TASK_EAGER_PROPAGATES = True

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
KWCOCO_ARCHIVES = []


class Command(BaseCommand):
    help = 'Populate database with demo data.'

    def _load_image_files(self, images):
        ids = []
        for imfile in images:
            if isinstance(imfile, (list, tuple)):
                result = self._load_image_files(imfile)
            else:
                path = datastore.fetch(imfile)
                model = models.imagery.ImageFile()
                model.file.save(os.path.basename(path), open(path, 'rb'))
                # Wait for ETL tasks to finish and get the ImageEntry ID
                result = model.baseimagefile_ptr.imageentry.pk
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
            images = models.ImageEntry.objects.filter(pk__in=pks).all()
            imset = models.ImageSet()
            imset.save()  # Have to save before adding to ManyToManyField
            for image in images:
                imset.images.add(image)
            imset.save()
            # Make raster of that image set
            raster = models.RasterEntry()
            raster.image_set = imset
            raster.save()
            ids.append(raster.pk)
        return ids

    def _load_shape_files(self):
        ids = []
        for shpfile in SHAPE_FILES:
            path = datastore.fetch(shpfile)
            model = models.GeometryArchive()
            model.file.save(os.path.basename(path), open(path, 'rb'))
            ids.append(model.geometryentry.pk)
        return ids

    def _load_fmv_files(self):
        raise NotImplementedError('FMV ETL with Docker is still broken.')

    def _load_kwcoco_archives(self):
        raise NotImplementedError()

    def handle(self, *args, **options):
        self._load_image_files(IMAGE_FILES)
        self._load_raster_files()
        self._load_shape_files()
        # self._load_fmv_files()
        # self._load_kwcoco_archives()
        self.stdout.write(self.style.SUCCESS(SUCCESS_MSG))
