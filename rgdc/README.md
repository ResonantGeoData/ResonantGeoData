# rgdc - ResonantGeoDataClient

The **rgdc** Python package allows users to make web requests to a ResonantGeoData instance within a Python script.


# Installation
```
pip install rgdc
```

# Usage
### Search and display results
```python
import json
import matplotlib.pyplot as plt
import numpy as np

from rgdc import Rgdc

def plot_geojson(gjs, *args, **kwargs):
    points = np.array(gjs['coordinates'][0])
    return plt.plot(points[:,0], points[:,1], *args, **kwargs)

client = Rgdc(username='username', password='password')
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

q = client.search(query=json.dumps(bbox), predicate='intersects', datatype='raster')

for s in q:
    print(s['subentry_name'])

plot_geojson(bbox, 'k--', label='Search Region')

for s in q:
    plot_geojson(s['footprint'], label=s['subentry_name'])

plt.legend()
plt.title(f'Count: {len(q)}')
```

### Inspect raster
```python
import imageio
from io import BytesIO
import requests

raster = requests.get(q[0]['detail']).json()
plot_geojson(bbox, 'k--')
plot_geojson(raster['outline'], 'r')
load_image = lambda imbytes: imageio.imread(BytesIO(imbytes))

count = len(raster['parent_raster']['image_set']['images'])
for i in range(count):
    thumb_bytes = client.download_raster_thumbnail(q[0], band=i)
    thumb = load_image(thumb_bytes)
    plt.subplot(1, count, i+1)
    plt.imshow(thumb)

plt.tight_layout()
plt.show()
```

### Download Raster
```python
import rasterio
from rasterio.plot import show

paths = client.download_raster(q[0])
rasters = [rasterio.open(im) for im in paths.images]
for i, src in enumerate(rasters):
    plt.subplot(1, count, i+1)
    ax = plt.gca()
    show(src, ax=ax)
plt.tight_layout()
plt.show()
```
