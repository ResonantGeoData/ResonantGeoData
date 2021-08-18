# [![logo](https://raw.githubusercontent.com/ResonantGeoData/ResonantGeoData/main/logos/RGD_Logo.png)](https://github.com/ResonantGeoData/ResonantGeoData/)

[![codecov](https://codecov.io/gh/ResonantGeoData/ResonantGeoData/branch/master/graph/badge.svg)](https://codecov.io/gh/ResonantGeoData/ResonantGeoData)
[![ci](https://github.com/ResonantGeoData/ResonantGeoData/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/ResonantGeoData/ResonantGeoData/actions/workflows/ci.yml)

> Geospatial Data API in Django

Resonant GeoData (RGD) is a series of Django applications well suited for cataloging and searching annotated geospatial imagery, shapefiles, and full motion video datasets.

A publicly deployed instance of this application is available at https://www.resonantgeodata.com - find the deployment code for this at [ResonantGeoData/RD-OpenGeo](https://github.com/ResonantGeoData/RD-OpenGeo)

![homepage](./docs/images/homepage.png)

## Highlights

- Faceted searching of spatiotemporal data
- Supports normal imagery and overhead raster imagery
- Supports image annotations: polygons, bounding boxes, keypoints, and run-length-encoded masks
- Built-in image tile server
- 3D viewer for point clouds and mesh files


## Documentation

Each app's README file contains an overview of functionality.

Documentation is currently a work in progress.

For general questions about the project, its applications, or about software usage, please create an issue directly in this repository. You are also welcome to send us an email at [rgd@kitware.com](mailto:rgd@kitware.com) with the subject line including Resonant GeoData.


## Connections

- Resonant GeoData is built on top of [Kitware's Girder 4 platform](https://github.com/search?q=topic%3Agirder-4+org%3Agirder+fork%3Atrue).
- [GeoJS](https://opengeoscience.github.io/geojs/): we leverage GeoJS for our interactive map view.
- [`large_image`](http://girder.github.io/large_image/index.html): we leverage `large_image` to serve image tiles and extract thumbnails.
- [VTK.js](https://kitware.github.io/vtk-js/): we use VTK.js for the client-side 3D viewer for 3D data.
- [KWIVER](https://github.com/Kitware/kwiver): we leverage KWIVER's Full Motion Video (FMV) processing capabilities to extract spatial information from FMV files.
- [KWCOCO](https://gitlab.kitware.com/computer-vision/kwcoco): KWCOCO is an extension of the [COCO image annotation format](https://cocodataset.org/) which we support for ingesting annotated imagery.


## Contributing

Please see the adjacent [`DEVELOPMENT.md`](https://github.com/ResonantGeoData/ResonantGeoData/blob/master/DEVELOPMENT.md) file for all development instructions.
