import pytest


@pytest.mark.django_db
def test_dataset_create(dataset):
    assert dataset


def test_dataset_name(dataset_factory):
    # Use "build" strategy, so database is not required
    dataset = dataset_factory.build()
    assert isinstance(dataset.name, str)
