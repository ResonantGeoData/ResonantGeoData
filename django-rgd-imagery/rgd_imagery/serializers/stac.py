import json

import dateutil.parser
from django.contrib.gis.geos import Polygon
from django.db import transaction
from pyproj import CRS
import pystac
from rest_framework import serializers
from rgd.models import ChecksumFile, FileSourceType
from rgd.utility import get_or_create_no_commit

from .. import models


class STACRasterSerializer(serializers.BaseSerializer):
    def to_internal_value(self, data):
        # item = pystac.Item.from_dict(data)
        # errors = item.validate()
        # if errors:
        #     raise serializers.ValidationError(errors)
        return data

    def to_representation(self, instance: models.RasterMeta) -> dict:
        item = pystac.Item(
            id=instance.pk,
            geometry=json.loads(instance.footprint.json),
            bbox=instance.extent,
            datetime=(instance.acquisition_date or instance.modified or instance.created),
            properties=dict(
                datetime=str(instance.acquisition_date),
                platform=instance.instrumentation,
            ),
        )
        # 'proj' extension
        item.ext.enable('projection')
        item.ext.projection.apply(
            epsg=CRS.from_proj4(instance.crs).to_epsg(),
            transform=instance.transform,
        )
        # 'eo' extension
        item.ext.enable('eo')
        item.ext.eo.apply(cloud_cover=instance.cloud_cover, bands=[])
        # Add assets
        band_num = 0
        for image in instance.parent_raster.image_set.images.all():
            if image.file.type != FileSourceType.URL:
                # TODO: we need fix this
                raise ValueError('Files must point to valid URL resources, not internal storage.')
            asset = pystac.Asset(
                href=image.file.get_url(),
                title=image.file.name,
                roles=[
                    'data',
                ],
            )
            if image.imagemeta.number_of_bands == 1:
                bands = [
                    pystac.extensions.eo.Band.create(
                        name=image.file.name,
                        description=image.bandmeta_set.first().description,
                    )
                ]
            else:
                bands = [
                    pystac.extensions.eo.Band.create(
                        name=f'B{bandmeta.band_number + band_num}',
                        description=bandmeta.description,
                    )
                    for bandmeta in image.bandmeta_set.all()
                ]
            item.ext.eo.set_bands(
                bands=bands,
                asset=asset,
            )
            item.add_asset(f'image-{image.pk}', asset)
            band_num += image.imagemeta.number_of_bands

        for ancillary_file in instance.parent_raster.ancillary_files.all():
            asset = pystac.Asset(
                href=ancillary_file.get_url(),
                title=ancillary_file.name,
                roles=[
                    'metadata',
                ],
            )
            item.add_asset(f'ancillary-{ancillary_file.pk}', asset)

        return item.to_dict()

    @transaction.atomic
    def create(self, data):
        item = pystac.Item.from_dict(data)
        image_ids, ancillary = [], []
        single_asset = False
        if len(item.assets) == 1:
            single_asset = True
        for name in item.assets:
            asset = item.assets[name]
            checksum_file, _ = ChecksumFile.objects.get_or_create(
                type=FileSourceType.URL,
                url=asset.href,
            )
            if single_asset or (asset.roles and 'data' in asset.roles):
                image, _ = models.Image.objects.get_or_create(file=checksum_file)
                image_ids.append(image.pk)
            else:
                ancillary.append(checksum_file)

        image_set, image_set_created = models.get_or_create_image_set(
            image_ids, defaults=dict(name=item.id)
        )

        raster, raster_created = get_or_create_no_commit(
            models.Raster, image_set=image_set, defaults=dict(name=item.id)
        )
        raster.skip_signal = True
        raster.save()
        [raster.ancillary_files.add(af) for af in ancillary]
        raster.save()

        outline = Polygon(
            (
                [item.bbox[0], item.bbox[1]],
                [item.bbox[0], item.bbox[3]],
                [item.bbox[2], item.bbox[3]],
                [item.bbox[2], item.bbox[1]],
                [item.bbox[0], item.bbox[1]],
            )
        )

        raster_meta = dict(
            footprint=json.dumps(item.geometry),
            crs=f'+init=epsg:{item.ext.projection.epsg}',
            cloud_cover=item.ext.eo.cloud_cover,
            transform=item.ext.projection.transform,
            extent=item.bbox,
            origin=(item.bbox[0], item.bbox[1]),
            resolution=(0, 0),  # TODO: fix
            outline=outline,
            acquisition_date=dateutil.parser.isoparser().isoparse(item.properties['datetime']),
            instrumentation=item.properties['platform'],
        )

        if raster_created:
            instance = models.RasterMeta(**raster_meta)
            instance.parent_raster = raster
        else:
            models.RasterMeta.objects.filter(parent_raster=raster).update(**raster_meta)
            instance = models.RasterMeta.objects.get(parent_raster=raster)
        instance.save()

        return instance
