import re
from typing import Generator, Optional

import boto3
import djclick as click


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
    s3_client = session.client("s3")

    for obj in _iter_matching_objects(
        s3_client, bucket, prefix, include_regex
    ):
        print(obj)
