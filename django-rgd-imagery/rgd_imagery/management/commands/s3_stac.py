from contextlib import contextmanager
import json
import multiprocessing
import os
import re
import tempfile
from typing import Generator, Optional

import boto3
from django.conf import settings
import djclick as click
from rgd_imagery.serializers import STACRasterSerializer


def _iter_matching_objects(
    s3_client,
    bucket: str,
    prefix: str,
    include_regex: str,
) -> Generator[dict, None, None]:
    paginator = s3_client.get_paginator('list_objects_v2')
    page_iter = paginator.paginate(Bucket=bucket, Prefix=prefix, RequestPayer='requester')
    include_pattern = re.compile(include_regex)

    for page in page_iter:
        for obj in page['Contents']:
            if include_pattern.match(obj['Key']):
                yield obj


@contextmanager
def download_object(s3_client, bucket, obj):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, 'stac.json')
        with open(path, 'wb') as f:
            s3_client.download_fileobj(bucket, obj['Key'], f)
        with open(path, 'r') as f:
            yield json.loads(f.read())


class STACLoader:
    def __init__(self, boto3_params, bucket: str):
        self.boto3_params = boto3_params
        self.bucket = bucket

    @property
    def client(self):
        session = boto3.Session(**self.boto3_params)
        return session.client('s3')

    def load_object(self, obj: dict) -> None:
        with download_object(self.client, self.bucket, obj) as data:
            STACRasterSerializer().create(data)


@click.command()
@click.argument('bucket')
@click.option('--include-regex', default=r'^.*\.json')
@click.option('--prefix', default='')
@click.option('--region', default='us-west-2')
@click.option('--access-key-id')
@click.option('--secret-access-key')
def ingest_s3(
    bucket: str,
    include_regex: str,
    prefix: str,
    region: str,
    access_key_id: Optional[str],
    secret_access_key: Optional[str],
) -> None:
    boto3_params = {
        'aws_access_key_id': access_key_id,
        'aws_secret_access_key': secret_access_key,
        'region_name': region,
    }

    session = boto3.Session(**boto3_params)
    s3_client = session.client('s3')

    _eager = getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False)
    _prop = getattr(settings, 'CELERY_TASK_EAGER_PROPAGATES', False)
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True

    loader = STACLoader(boto3_params, bucket)
    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool.map(
        loader.load_object,
        _iter_matching_objects(s3_client, bucket, prefix, include_regex),
    )

    # Reset celery to previous settings
    settings.CELERY_TASK_ALWAYS_EAGER = _eager
    settings.CELERY_TASK_EAGER_PROPAGATES = _prop
