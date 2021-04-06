import re
from typing import Generator, Optional

import boto3
import botocore
import djclick as click


def _iter_matching_objects(
    s3_client, bucket: str, prefix: str, include_regex: str
) -> Generator[dict, None, None]:
    paginator = s3_client.get_paginator('list_objects')
    page_iter = paginator.paginate(Bucket=bucket, Prefix=prefix)
    include_pattern = re.compile(include_regex)

    for page in page_iter:
        for obj in page['Contents']:
            if include_pattern.match(obj['Key']):
                yield obj


@click.command()
@click.argument('bucket')
@click.option('--include-regex', default='')
@click.option('--prefix', default='')
@click.option('--region', default='us-east-1')
@click.option('--access-key-id')
@click.option('--secret-access-key')
@click.option('--google', is_flag=True, default=False)
def ingest_s3(
    bucket: str,
    include_regex: str,
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
    for obj in _iter_matching_objects(s3_client, bucket, prefix, include_regex):
        print(obj['Key'])  # TODO create database record(s)
