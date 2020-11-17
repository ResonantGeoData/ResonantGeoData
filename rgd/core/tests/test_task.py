import pytest


@pytest.mark.skip
@pytest.mark.django_db
def test_get_absolute_url(task):
    # This will also fail if the urlconf is not defined.
    assert task.get_absolute_url().startswith('/task/1-')
