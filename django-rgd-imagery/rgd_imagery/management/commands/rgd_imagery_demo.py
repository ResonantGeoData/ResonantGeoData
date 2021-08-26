from rgd.management.commands._data_helper import SynchronousTasksCommand

from . import _data_helper as helper

SUCCESS_MSG = 'Finished loading all demo data.'

# Names of files in the datastore
RASTER_FILES = [
    ['20091021202517-01000100-VIS_0001.ntf'],
    ['aerial_rgba_000003.tiff'],
    ['cclc_schu_100.tif'],
    ['landcover_sample_2000.tif'],
    ['paris_france_10.tiff'],
    ['rgb_geotiff.tiff'],
    ['RomanColosseum_WV2mulitband_10.tif'],
    [
        'LC08_L1TP_034032_20200429_20200509_01_T1_sr_band1.tif',
        'LC08_L1TP_034032_20200429_20200509_01_T1_sr_band2.tif',
        'LC08_L1TP_034032_20200429_20200509_01_T1_sr_band3.tif',
    ],
    ['Elevation.tif'],
    ['L1C_T13SCD_A019901_20201227T175922.tif'],
    ['L1C_T18TWN_A016525_20200505T155731.tif'],
    ['L1C_T18TWN_A018527_20200922T155115.tif'],
    ['L1C_T18TWN_A025648_20200520T155359.tif'],
    ['L1C_T18TWN_A027793_20201017T155552.tif'],
    ['L1C_T18TWN_A028079_20201106T160014.tif'],
    # ['bpasg_emodis_week34_082320.tif'],
    # ['vegdri_diff_2020_34_gtif.tif'],
    # ['vegdri_emodis_week34_082320.tif'],
    # ['US_eMAH_NDVI.2020.350-356.1KM.VI_ACQI.006.2020359165956.tif'],
    # ['US_eMAH_NDVI.2020.350-356.1KM.VI_NDVI.006.2020359165956.tif'],
    # ['US_eMAH_NDVI.2020.350-356.1KM.VI_QUAL.006.2020359165956.tif'],
    ['TC_NG_SFBay_US_Geo.tif'],
]
KWCOCO_ARCHIVES = [['demo.kwcoco.json', 'demodata.zip'], ['demo_rle.kwcoco.json', 'demo_rle.zip']]
SPATIAL_IMAGE_SETS = [
    (
        ['afie_1.jpg', 'afie_2.jpg', 'afie_3.jpg'],
        'afie.geojson',
    )
]


class Command(SynchronousTasksCommand):
    help = 'Populate database with demo data.'

    def handle(self, *args, **options):
        self.set_synchronous()
        # Run the command
        helper.load_raster_files([helper.make_raster_dict(im) for im in RASTER_FILES])
        helper.load_kwcoco_archives(KWCOCO_ARCHIVES)
        helper.load_spatial_image_sets(SPATIAL_IMAGE_SETS)
        self.stdout.write(self.style.SUCCESS(SUCCESS_MSG))
        self.reset_celery()
