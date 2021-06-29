from rgd import datastore


def test_datastore_format():
    """Validates that all entries in the datastore are formatted correctly."""
    for k, v in datastore.registry.items():
        c = v.split(':')
        assert len(c) == 2, f'`{k}` improperly formatted.'


def test_datastore_valid():
    """Validates that all entries in the datastore are available for download."""
    for k in datastore.registry.keys():
        assert datastore.datastore.is_available(k), f'`{k}` not available.'
