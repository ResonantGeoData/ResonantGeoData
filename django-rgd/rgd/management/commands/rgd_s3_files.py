import multiprocessing
import re
from typing import Generator, Optional

import boto3
import botocore
import djclick as click

from . import _data_helper as helper


def _iter_matching_objects(
    s3_client,
    bucket: str,
    prefix: str,
    include_regex: str,
    exclude_regex: str,
) -> Generator[dict, None, None]:
    paginator = s3_client.get_paginator('list_objects_v2')
    page_iter = paginator.paginate(Bucket=bucket, Prefix=prefix)
    include_pattern = re.compile(include_regex)
    exclude_pattern = re.compile(exclude_regex)

    for page in page_iter:
        for obj in page['Contents']:
            if include_pattern.match(obj['Key']) and not exclude_pattern.search(obj['Key']):
                yield obj


class Loader:
    def __init__(self, bucket: str, region: str, google: bool = False):
        self.bucket = bucket
        self.google = google
        self.region = region

    def _format_url(self, base_url):
        if self.google:
            return f'http://storage.googleapis.com/{base_url}'
        return f'https://{self.region}.amazonaws.com/{base_url}'

    def load_object(self, obj: dict) -> None:
        key = obj['Key']
        url = self._format_url(f'{self.bucket}/{key}')
        helper._get_or_create_checksum_file_url(url, name=key)


@click.command()
@click.argument('bucket')
@click.option('--include-regex', default='')
@click.option('--exclude-regex', default='')
@click.option('--prefix', default='')
@click.option('--region', default='us-east-1')
@click.option('--access-key-id')
@click.option('--secret-access-key')
@click.option('--google', is_flag=True, default=False)
def ingest_s3(
    bucket: str,
    include_regex: str,
    exclude_regex: str,
    prefix: str,
    region: str,
    access_key_id: Optional[str],
    secret_access_key: Optional[str],
    google: bool,
) -> None:
    if access_key_id and secret_access_key:
        boto3_params = {
            'aws_access_key_id': access_key_id,
            'aws_secret_access_key': secret_access_key,
            'config': botocore.client.Config(signature_version='s3v4', region_name=region),
        }
    else:
        boto3_params = {
            'config': botocore.client.Config(
                signature_version=botocore.UNSIGNED, region_name=region
            )
        }

    if google:  # Google Cloud Storage
        boto3_params['endpoint_url'] = 'https://storage.googleapis.com'

    s3_client = boto3.client('s3', **boto3_params)

    loader = Loader(bucket, region, google=google)
    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool.map(
        loader.load_object,
        _iter_matching_objects(s3_client, bucket, prefix, include_regex, exclude_regex),
    )
