import re

import pytest


@pytest.mark.django_db(transaction=True)
def test_stac_browser_limit(settings, admin_api_client, sample_raster_url):
    response = admin_api_client.get('/api/stac/collection/default/items')
    assert response.status_code == 200
    settings.RGD_STAC_BROWSER_LIMIT = 1
    with pytest.raises(
        ValueError,
        match=re.escape(
            "'RGD_STAC_BROWSER_LIMIT' (1) exceeded. Requested collection with 3 items."
        ),
    ):
        response = admin_api_client.get('/api/stac/collection/default/items')
