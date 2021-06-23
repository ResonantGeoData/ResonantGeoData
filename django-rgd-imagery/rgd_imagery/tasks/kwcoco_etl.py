import os
import tempfile
import zipfile

from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.gis.geos import LineString, MultiPoint, MultiPolygon, Point, Polygon
import kwcoco
import kwimage
import numpy as np
from rgd.models import ChecksumFile
from rgd_imagery.models import (
    Annotation,
    Image,
    ImageSet,
    KWCOCOArchive,
    PolygonSegmentation,
    RLESegmentation,
    Segmentation,
)

logger = get_task_logger(__name__)


def _fill_annotation_segmentation(annotation_entry, ann_json):
    """For converting KWCOCO annotation JSON to an Annotation entry."""
    if 'keypoints' in ann_json and ann_json['keypoints']:
        # populate keypoints - ignore 3rd value visibility
        logger.info('Keypoints: {}'.format(ann_json['keypoints']))
        points = np.array(ann_json['keypoints']).astype(float).reshape((-1, 3))
        keypoints = []
        for pt in points:
            logger.info(f'The Point: {pt}')
            keypoints.append(Point(pt[0], pt[1]))
        annotation_entry.keypoints = MultiPoint(*keypoints)
    if 'line' in ann_json and ann_json['line']:
        # populate line
        points = np.array(ann_json['line']).astype(float).reshape((-1, 2))
        logger.info(f'The line: {points}')
        annotation_entry.line = LineString(*[(pt[0], pt[1]) for pt in points], srid=0)
    # Add a segmentation
    segmentation = None
    if 'segmentation' in ann_json and ann_json['segmentation']:
        sseg = kwimage.Segmentation.coerce(ann_json['segmentation']).data
        if isinstance(sseg, kwimage.Mask):
            segmentation = RLESegmentation()
            segmentation.from_rle(ann_json['segmentation'])
        else:
            segmentation = PolygonSegmentation()
            polys = []
            multipoly = sseg.to_multi_polygon()
            for poly in multipoly.data:
                poly_xys = poly.data['exterior'].data
                # Close the loop
                poly_xys = np.append(poly_xys, poly_xys[0][None], axis=0)
                polys.append(Polygon(poly_xys, srid=0))
            segmentation.feature = MultiPolygon(*polys)
    if 'bbox' in ann_json and ann_json['bbox']:
        if not segmentation:
            segmentation = Segmentation()  # Simple outline segmentation
        # defined as (x, y, width, height)
        x0, y0, w, h = np.array(ann_json['bbox'])
        points = [
            [x0, y0],
            [x0, y0 + h],
            [x0 + w, y0 + h],
            [x0 + w, y0],
            [x0, y0],  # close the loop
        ]
        segmentation.outline = Polygon(points, srid=0)
    annotation_entry.save()
    # Save if a segmentation is used
    if segmentation:
        segmentation.annotation = annotation_entry
        segmentation.save()


def load_kwcoco_dataset(kwcoco_dataset_id):
    logger.info('Starting KWCOCO ETL routine')
    ds_entry = KWCOCOArchive.objects.get(id=kwcoco_dataset_id)
    if not ds_entry.name:
        ds_entry.name = os.path.basename(ds_entry.spec_file.name)
        ds_entry.save(
            update_fields=[
                'name',
            ]
        )

    # TODO: add a setting like this:
    workdir = getattr(settings, 'GEODATA_WORKDIR', None)
    with tempfile.TemporaryDirectory(dir=workdir) as tmpdir:

        if ds_entry.image_set:
            # Delete all previously existing data
            # This should cascade to all the annotations
            for image in ds_entry.image_set.images.all():
                image.file.delete()
        else:
            ds_entry.image_set = ImageSet()
        ds_entry.image_set.name = ds_entry.name
        ds_entry.image_set.save()
        ds_entry.save(
            update_fields=[
                'image_set',
            ]  # noqa: E231
        )

        # Unarchive the images locally so we can import them when loading the spec
        # Images could come from a URL, so this is optional
        if ds_entry.image_archive:
            with ds_entry.image_archive.file as file_obj:
                logger.info(f'The KWCOCO image archive: {ds_entry.image_archive}')
                # Place images in a local directory and keep track of root path
                # Unzip the contents to the working dir
                with zipfile.ZipFile(file_obj, 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)
                logger.info(f'The extracted KWCOCO image archive: {tmpdir}')
        else:
            pass
            # TODO: how should we download data from specified URLs?

        # Load the KWCOCO JSON spec and make annotations on the images
        with ds_entry.spec_file.yield_local_path() as file_path:
            ds = kwcoco.CocoDataset(str(file_path))
            # Set the root dir to where the images were extracted / the temp dir
            # If images are coming from URL, they will download to here
            ds.img_root = tmpdir
            # Iterate over images and create an ImageMeta from them.
            # Any images in the archive that aren't listed in the JSON will be deleted
            for imgid in ds.imgs.keys():
                ak = ds.index.gid_to_aids[imgid]
                img = ds.imgs[imgid]
                anns = [ds.anns[k] for k in ak]
                # Create the Image entry to track each image's location
                image_file_abs_path = os.path.join(ds.img_root, img['file_name'])
                name = os.path.basename(image_file_abs_path)
                file = ChecksumFile()
                file.file.save(name, open(image_file_abs_path, 'rb'))
                image, _ = Image.objects.get_or_create(file=file)
                # Add ImageMeta to ImageSet
                ds_entry.image_set.images.add(image)
                # Create annotations that link to that ImageMeta
                for ann in anns:
                    annotation_entry = Annotation()
                    annotation_entry.image = image
                    try:
                        annotation_entry.label = ds.cats[ann['category_id']]['name']
                    except KeyError:
                        pass
                    # annotation_entry.annotator =
                    # annotation_entry.notes =
                    _fill_annotation_segmentation(annotation_entry, ann)
    logger.info('Done with KWCOCO ETL routine')
