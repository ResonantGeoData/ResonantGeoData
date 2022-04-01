import json

from django.test import Client
from django.urls import reverse
import pytest
from pytest_django.asserts import assertContains


@pytest.mark.django_db(transaction=True)
def test_search_request_body(admin_client: Client):
    q = {'type': 'Point', 'coordinates': [-55.10921003348354, 40.94760151752767]}
    predicate = 'intersects'
    resp = admin_client.get(reverse('rgd-index'), data=dict(q=json.dumps(q), predicate=predicate))

    for coordinate in q['coordinates']:
        assertContains(resp, coordinate)
