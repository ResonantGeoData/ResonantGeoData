ROLE_CHOICES = [
    (
        'Item Spec',
        (
            (
                'thumbnail',
                (
                    'An asset that represents a thumbnail of the item, '
                    'typically a true color image (for items with assets '
                    'in the visible wavelengths), lower-resolution '
                    '(typically smaller 600x600 pixels), and typically '
                    'a JPEG or PNG (suitable for display in a web browser). '
                    'Multiple assets may have this purpose, but it is '
                    'recommended that the type and roles be unique tuples. '
                    'For example, Sentinel-2 L2A provides thumbnail images '
                    'in both JPEG and JPEG2000 formats, and would be '
                    'distinguished by their media types.'
                ),
            ),
            (
                'data',
                (
                    'The data itself. This is a suggestion for a common role '
                    "for data files to be used in case data providers don't "
                    'come up with their own names and semantics.'
                ),
            ),
            (
                'metadata',
                (
                    'A metadata sidecar file describing the data in this item, for '
                    'example the Landsat-8 MTL file.'
                ),
            ),
        ),
    ),
    (
        'Best Practice',
        (
            (
                'visual',
                (
                    'An asset that is a full resolution version of the data, '
                    'processed for visual use (RGB only, often sharpened '
                    '(pan-sharpened and/or using an unsharp mask)).',
                ),
            ),
            (
                'date',
                (
                    'An asset that provides per-pixel acquisition timestamps, '
                    'typically serving as metadata to another asset',
                ),
            ),
            (
                'graphic',
                'Supporting plot, illustration, or graph associated with the Item',
            ),
            (
                'data-mask',
                (
                    'File indicating if corresponding pixels have Valid data '
                    'and various types of invalid data',
                ),
            ),
            (
                'snow-ice',
                (
                    'Points to a file that indicates whether a pixel is '
                    'assessed as being snow/ice or not'
                ),
            ),
            (
                'land-water',
                (
                    'Points to a file that indicates whether a pixel is '
                    'assessed being land or water'
                ),
            ),
            (
                'water-mask',
                (
                    'Points to a file that indicates whether a pixel is '
                    'assessed as being water (e.g. flooding map)'
                ),
            ),
        ),
    ),
]

TYPE_CHOICES = [
    ('image/tiff; application=geotiff', 'GeoTIFF with standardized georeferencing metadata'),
    (
        'image/tiff; application=geotiff; profile=cloud-optimized',
        'Cloud Optimized GeoTIFF (unofficial)',
    ),
    ('image/jp2', 'JPEG 2000'),
    ('image/png', 'Visual PNGs (e.g. thumbnails)'),
    ('image/jpeg', 'Visual JPEGs (e.g. thumbnails, oblique)'),
    ('text/xml', 'XML metadata RFC 7303'),
    ('application/json', 'A JSON file (often metadata, or labels)'),
    ('text/plain', 'Plain text (often metadata)'),
    ('application/geo+json', 'GeoJSON'),
    ('application/geopackage+sqlite3', 'GeoPackage'),
    ('application/x-hdf5', 'Hierarchical Data Format version 5'),
    ('application/x-hdf', 'Hierarchical Data Format versions 4 and earlier'),
]
