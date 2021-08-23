import logging
import os
from urllib.parse import urljoin

import djclick as click
from rgd.utility import url_file_to_local_path

from . import _data_helper as helper

logger = logging.getLogger(__name__)


@click.command()
@click.option('-h', '--host', default='http://sitemap:8081')
def ingest_s3(
    host: str,
) -> None:
    with url_file_to_local_path(urljoin(host, 'sitemap.txt')) as file:
        with open(file, 'r') as f:
            for path in f.readlines():
                name = os.path.basename(path)
                url = urljoin(host, path)
                logger.info(url)
                helper._get_or_create_checksum_file_url(url, name=name, validate=False)
