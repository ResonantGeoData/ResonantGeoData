[![logo](https://raw.githubusercontent.com/ResonantGeoData/ResonantGeoData/main/logos/RGD_Logo.png)](https://github.com/ResonantGeoData/ResonantGeoData/)

# rgd_client - Resonant GeoDataClient

The **rgd_client** Python package is a well typed, easy to use, and extendable Python client for Resonant GeoData APIs.


# Installation

To install the core client
```
pip install rgd-client
```

To use other core modules or plugins, install the corresponding client packages. For example, the imagery client plugin is installed with
```
pip install rgd-imagery-client
```

All the functions added via a plugin are namespaced under a name defined by that plugin. For the imagery client plugin, this is `imagery`, so all of these plugin's features are accessed through `client.imagery.*`. Examples of this are shown below.

# Usage
### Search and display results
```python
import json
import matplotlib.pyplot as plt
import numpy as np

from rgd_client import create_rgd_client

def plot_geojson(gjs, *args, **kwargs):
    points = np.array(gjs['coordinates'])
    if points.ndim == 3:
        points = points[0]
    if points.ndim == 1:
        points = points.reshape((1, points.size, ))
    return plt.plot(points[:,0], points[:,1], *args, **kwargs)

client = create_rgd_client(username='username', password='password')
bbox = {
    "type":"Polygon",
    "coordinates":[
        [
            [-105.45091240368326,39.626245373878696],
            [-105.45091240368326,39.929904289147274],
            [-104.88775649170178,39.929904289147274],
            [-104.88775649170178,39.626245373878696],
            [-105.45091240368326,39.626245373878696]
        ]
    ]
}

q = client.rgd.search(query=json.dumps(bbox), predicate='intersects')

for s in q:
    print(s['subentry_name'])

plot_geojson(bbox, 'k--', label='Search Region')

for s in q:
    plot_geojson(s['footprint'], label=s['subentry_name'])

plt.legend()
plt.title(f'Count: {len(q)}')
```

### Inspect raster

Preview thumbnails of the raster

```python
import imageio
from io import BytesIO

raster = client.imagery.get_raster(q[0])
plot_geojson(bbox, 'k--')
plot_geojson(raster['outline'], 'r')
load_image = lambda imbytes: imageio.imread(BytesIO(imbytes))

count = len(raster['parent_raster']['image_set']['images'])
for i in range(count):
    thumb_bytes = client.imagery.download_raster_thumbnail(q[0], band=i)
    thumb = load_image(thumb_bytes)
    plt.subplot(1, count, i+1)
    plt.imshow(thumb)

plt.tight_layout()
plt.show()
```

### Download Raster

Download the entire image set of the raster

```python
import rasterio
from rasterio.plot import show

paths = client.imagery.download_raster(q[0])
rasters = [rasterio.open(im) for im in paths.images]
for i, src in enumerate(rasters):
    plt.subplot(1, len(rasters), i+1)
    ax = plt.gca()
    show(src, ax=ax)
plt.tight_layout()
plt.show()
```


### STAC Item Support

The Python client has a search endpoint specifically for Raster data that
returns each record in the search results as a STAC Item.

```py

q = client.imagery.search_raster_stac(query=json.dumps(bbox), predicate='intersects')

print(q[0])  # view result as STAC Item

# Download using the search result
paths = client.imagery.download_raster(q[0])
print(paths)

```

We can also upload new data in the STAC Item format. Here we simply pass back
the same STAC Item JSON which will not actually do anything because RGD
recognizes that these files are already present with a Raster.

```py
client.imagery.create_raster_stac(q[0])
```

Please note that the assets in the STAC Item must already be uploaded to a
cloud storage provider with either `s3://` or `https://` URLs. Further, the
images must have the `data` tag on each asset. e.g.:

```py
{
    ... # other STAC Item fields
    'assets': {
        'image-15030': {
            'href': 'http://storage.googleapis.com/gcp-public-data-sentinel-2/tiles/17/S/MS/S2A_MSIL1C_20210302T161201_N0209_R140_T17SMS_20210302T200521.SAFE/GRANULE/L1C_T17SMS_A029738_20210302T161751/IMG_DATA/T17SMS_20210302T161201_B01.jp2',
            'title': 'GRANULE/L1C_T17SMS_A029738_20210302T161751/IMG_DATA/T17SMS_20210302T161201_B01.jp2',
            'eo:bands': [{'name': 'B1'}],
            'roles': ['data'],
        },
        'image-15041': {
            'href': 'http://storage.googleapis.com/gcp-public-data-sentinel-2/tiles/17/S/MS/S2A_MSIL1C_20210302T161201_N0209_R140_T17SMS_20210302T200521.SAFE/GRANULE/L1C_T17SMS_A029738_20210302T161751/IMG_DATA/T17SMS_20210302T161201_B02.jp2',
            'title': 'GRANULE/L1C_T17SMS_A029738_20210302T161751/IMG_DATA/T17SMS_20210302T161201_B02.jp2',
            'eo:bands': [{'name': 'B1'}],
            'roles': ['data'],
        },
        ...  # ancillary files can lack a role but we like to see `metadata` used.
        'ancillary-30687': {
            'href': 'http://storage.googleapis.com/gcp-public-data-sentinel-2/tiles/17/S/MS/S2A_MSIL1C_20210302T161201_N0209_R140_T17SMS_20210302T200521.SAFE/GRANULE/L1C_T17SMS_A029738_20210302T161751/QI_DATA/MSK_TECQUA_B03.gml',
            'title': 'GRANULE/L1C_T17SMS_A029738_20210302T161751/QI_DATA/MSK_TECQUA_B03.gml',
            'roles': ['metadata'],
        },
    }
}
```

# Plugin Development
For instructions on how to develop a plugin for `rgd_client`, see `PLUGINS.md`.
