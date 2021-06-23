from datetime import datetime
import logging
import multiprocessing
import os
import tempfile
import xml.etree.ElementTree as ElementTree

import pandas as pd
from rgd import datastore
from rgd.management.commands._data_helper import SynchronousTasksCommand
from rgd.utility import safe_urlopen

from . import _data_helper as helper

logger = logging.getLogger(__name__)

SUCCESS_MSG = 'Finished loading all {} data.'


def _fetch_landsat_index_table():
    path = datastore.datastore.fetch('landsat.csv')
    return pd.read_csv(path)


def _fetch_sentinel_index_table():
    path = datastore.datastore.fetch('sentinel.csv')
    df = pd.read_csv(path)
    # Handle issue where tiles for a given date were processed multiple times
    #   to avoid ingesting duplicate data.
    clean = df.sort_values('PRODUCT_ID').drop_duplicates(
        ['MGRS_TILE', 'SENSING_TIME'], keep='first'
    )
    return clean.sort_index()


def _format_gs_base_url(base_url):
    return 'http://storage.googleapis.com/' + base_url.replace('gs://', '')


def _get_landsat_urls(base_url, name, sensor='TM'):
    if sensor == 'OLI_TIRS':  # Landsat 8
        possible_bands = [
            'B1.TIF',
            'B2.TIF',
            'B3.TIF',
            'B4.TIF',
            'B5.TIF',
            'B6.TIF',
            'B7.TIF',
            'B8.TIF',
            'B9.TIF',
            'B10.TIF',
            'B11.TIF',
            'BQA.TIF',
        ]
        possible_anc = [
            'ANG.txt',
            'MTL.txt',
        ]
    elif sensor == 'ETM':  # Landsat 7
        possible_bands = [
            'B1.TIF',
            'B2.TIF',
            'B3.TIF',
            'B4.TIF',
            'B5.TIF',
            # 'B6.TIF',
            'B6_VCID_1.TIF',
            'B6_VCID_2.TIF',
            'B7.TIF',
            'B8.TIF',
            # 'B9.TIF',
            'BQA.TIF',
        ]
        possible_anc = [
            'ANG.txt',
            'MTL.txt',
        ]
    else:
        raise ValueError(f'Unknown sensor: {sensor}')
    base_url = _format_gs_base_url(base_url)
    # Return tuples of (path, URL) : path is what is saved to model name field
    # this path should encompass the relative path of the files for the raster
    urls = [(None, base_url + '/' + name + '_' + band) for band in possible_bands]
    ancillary = [(None, base_url + '/' + name + '_' + ext) for ext in possible_anc]
    return urls, ancillary


def _load_landsat(row):
    urls, ancillary = _get_landsat_urls(row['BASE_URL'], row['PRODUCT_ID'], row['SENSOR_ID'])
    rd = helper.make_raster_dict(
        urls,
        date=row['SENSING_TIME'],
        name=row['PRODUCT_ID'],
        cloud_cover=row['CLOUD_COVER'],
        ancillary_files=ancillary,
        instrumentation=row['SENSOR_ID'],
    )
    return rd


def _get_sentinel_urls(base_url):
    base_url = _format_gs_base_url(base_url)
    manifest_url = base_url + '/manifest.safe'
    with safe_urlopen(manifest_url) as remote, tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = os.path.join(tmpdir, 'manifest.safe')
        with open(manifest_path, 'wb') as f:
            f.write(remote.read())
        # Now check to see if `MTD_TL.xml` is in the manifest ONCE - if more or less, skip it.
        # Ask Matthew Bernstein for insight
        with open(manifest_path, 'r') as f:
            if f.read().count('MTD_TL.xml') != 1:
                raise ValueError('This entry is bad.')
        tree = ElementTree.parse(manifest_path)

    urls = []
    ancillary = []
    # Return tuples of (path, URL) : path is what is saved to model name field
    # this path should encompass the relative path of the files for the raster
    root = tree.getroot()
    meta = root.find('dataObjectSection')
    for c in meta:
        f = c.find('byteStream').find('fileLocation')
        href = f.attrib['href'][2::]  # to remove `./`
        di = href.split('/')[0]
        if di in [
            'GRANULE',
        ]:
            url = base_url + '/' + href
            if url[-4:] == '.jp2':
                urls.append((href, url))
            else:
                ancillary.append((href, url))

    return urls, ancillary


def _load_sentinel(row):
    urls, ancillary = _get_sentinel_urls(row['BASE_URL'])
    rd = helper.make_raster_dict(
        urls,
        date=row['SENSING_TIME'],
        name=row['PRODUCT_ID'],
        cloud_cover=row['CLOUD_COVER'],
        ancillary_files=ancillary,
        instrumentation=row['PRODUCT_ID'].split('_')[0],
    )
    return rd


class GCLoader:
    def __init__(self, satellite, footprint=False):
        if satellite not in ['landsat', 'sentinel']:
            raise ValueError(f'Unknown satellite {satellite}.')
        self.satellite = satellite

        if self.satellite == 'landsat':
            self.index = _fetch_landsat_index_table()
        elif self.satellite == 'sentinel':
            self.index = _fetch_sentinel_index_table()

        self.footprint = footprint

    def _load_raster(self, index):
        row = self.index.iloc[index]
        try:
            if self.satellite == 'landsat':
                rd = _load_landsat(row)
            elif self.satellite == 'sentinel':
                rd = _load_sentinel(row)
        except ValueError:
            return None
        imentries = helper.load_images(rd.get('images'))
        helper.load_raster(imentries, rd, footprint=self.footprint)

    def load_rasters(self, count=None):
        if not count:
            count = len(self.index)
        logger.info(f'Processing {count} rasters...')
        pool = multiprocessing.Pool(multiprocessing.cpu_count())
        pool.map(self._load_raster, range(count))


class Command(SynchronousTasksCommand):
    help = 'Populate database with demo landsat data from S3.'

    def add_arguments(self, parser):
        parser.add_argument('satellite', type=str, help='landsat or sentinel')
        parser.add_argument(
            '-c', '--count', type=int, help='Indicates the number scenes to fetch.', default=None
        )
        parser.add_argument(
            '-f',
            '--footprint',
            action='store_true',
            default=False,
            help='Compute the valid data footprints',
        )

    def handle(self, *args, **options):
        self.set_synchronous()

        count = options.get('count', None)
        satellite = options.get('satellite')
        footprint = options.get('footprint')

        start_time = datetime.now()

        loader = GCLoader(satellite, footprint=footprint)
        loader.load_rasters(count)

        self.stdout.write(
            self.style.SUCCESS('--- Completed in: {} ---'.format(datetime.now() - start_time))
        )
        self.stdout.write(self.style.SUCCESS(SUCCESS_MSG.format(satellite)))
        self.reset_celery()
