from pooch.processors import Unzip
import pytest
from rgd.datastore import datastore
from rgd_3d.models.tiles import Tiles3DMeta, create_tiles3d_from_paths

TOLERANCE = 2e-2

centroids = {
    'jacksonville-untextured.zip': {'x': -81.6634, 'y': 30.3234},
    'jacksonville-textured.zip': {'x': -81.6634, 'y': 30.3234},
    'jacksonville-point-cloud-3d-tiles.zip': {'x': -81.6634, 'y': 30.3234},
    'dragon.zip': {'x': -75.6079, 'y': 40.0439},
}


@pytest.mark.parametrize(
    'sample_file',
    [
        'jacksonville-untextured.zip',
        'jacksonville-textured.zip',
        'jacksonville-point-cloud-3d-tiles.zip',
        'dragon.zip',
    ],
)
@pytest.mark.django_db(transaction=True)
def test_tiles_3d_etl(sample_file):
    paths = datastore.fetch(sample_file, processor=Unzip())

    entry = create_tiles3d_from_paths(paths)
    entry.refresh_from_db()

    meta = Tiles3DMeta.objects.get(source=entry)

    assert meta.footprint is not None
    centroid = meta.outline.centroid
    assert centroid.x == pytest.approx(centroids[sample_file]['x'], abs=TOLERANCE)
    assert centroid.y == pytest.approx(centroids[sample_file]['y'], abs=TOLERANCE)
