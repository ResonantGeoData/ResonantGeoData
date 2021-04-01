from datetime import datetime
import os
import tempfile
import xml.etree.ElementTree as ElementTree

import pandas as pd

from rgd.geodata import datastore
from rgd.utility import safe_urlopen

from . import _data_helper as helper

SUCCESS_MSG = 'Finished loading all {} data.'


def _fetch_landsat_index_table():
    # https://data.kitware.com/#item/605cbf9c2fa25629b9e15c5c
    path = datastore.datastore.fetch('landsat_korea.csv')
    return pd.read_csv(path)


def _fetch_sentinel_index_table():
    # https://data.kitware.com/#item/6064f7e92fa25629b9319906
    path = datastore.datastore.fetch('sentinel_korea.csv')
    return pd.read_csv(path)


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
    urls = [base_url + '/' + name + '_' + band for band in possible_bands]
    ancillary = [base_url + '/' + name + '_' + ext for ext in possible_anc]
    return urls, ancillary


def _get_landsat_raster_dicts(count=0):
    index = _fetch_landsat_index_table()
    rasters = []
    i = 0
    for _, row in index.iterrows():
        urls, ancillary = _get_landsat_urls(row['BASE_URL'], row['PRODUCT_ID'], row['SENSOR_ID'])
        rasters.append(
            helper.make_raster_dict(
                urls,
                date=row['SENSING_TIME'],
                name=row['PRODUCT_ID'],
                cloud_cover=row['CLOUD_COVER'],
                ancillary_files=ancillary,
                instrumentation=row['SENSOR_ID'],
            )
        )
        if count > 0 and i >= count - 1:
            break
        i += 1
    return rasters


def _get_sentinel_urls(base_url, granule_id):
    base_url = _format_gs_base_url(base_url)
    manifest_url = base_url + '/manifest.safe'
    with safe_urlopen(manifest_url) as remote, tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = os.path.join(tmpdir, 'manifest.safe')
        with open(manifest_path, 'wb') as f:
            f.write(remote.read())
        tree = ElementTree.parse(manifest_path)

    urls = []
    ancillary = []

    root = tree.getroot()
    meta = root.find('dataObjectSection')
    for c in meta:
        f = c.find('byteStream').find('fileLocation')
        href = f.attrib['href'][1::]  # to remove `.`
        di = href.split('/')[1]
        if di in [
            'GRANULE',
        ]:
            url = base_url + href
            if url[-4:] == '.jp2':
                urls.append(url)
            else:
                ancillary.append(url)

    return urls, ancillary


def _get_sentinel_raster_dicts(count=0):
    index = _fetch_sentinel_index_table()
    rasters = []
    i = 0
    for _, row in index.iterrows():
        urls, ancillary = _get_sentinel_urls(row['BASE_URL'], row['GRANULE_ID'])
        rasters.append(
            helper.make_raster_dict(
                urls,
                date=row['SENSING_TIME'],
                name=row['PRODUCT_ID'],
                cloud_cover=row['CLOUD_COVER'],
                ancillary_files=ancillary,
                instrumentation=row['PRODUCT_ID'].split('_')[0],
            )
        )
        if count > 0 and i >= count - 1:
            break
        i += 1
    return rasters


class Command(helper.SynchronousTasksCommand):
    help = 'Populate database with demo landsat data from S3.'

    def add_arguments(self, parser):
        parser.add_argument('satellite', type=str, help='landsat or sentinel')
        parser.add_argument('-c', '--count', type=int, help='Indicates the number scenes to fetch.')

    def handle(self, *args, **options):
        self.set_synchronous()

        count = options.get('count', 0)
        satellite = options.get('satellite')

        if satellite == 'landsat':
            data = _get_landsat_raster_dicts(count)
        elif satellite == 'sentinel':
            data = _get_sentinel_raster_dicts(count)
        else:
            raise ValueError(f'Unknown satellite {satellite}.')

        # Run the command
        start_time = datetime.now()
        helper.load_raster_files(data)
        self.stdout.write(
            self.style.SUCCESS('--- Completed in: {} ---'.format(datetime.now() - start_time))
        )
        self.stdout.write(self.style.SUCCESS(SUCCESS_MSG.format(satellite)))
        self.reset_celery()
