import logging
from typing import List

import djclick as click
from rgd.models import WhitelistedEmail

logger = logging.getLogger(__name__)


@click.command()
@click.option('-e', '--email', multiple=True)
def ingest_s3(
    email: List[str],
) -> None:
    for e in email:
        e = e.strip()
        logger.info(f'Whitelisting `{e}`')
        WhitelistedEmail.objects.get_or_create(email=e)
