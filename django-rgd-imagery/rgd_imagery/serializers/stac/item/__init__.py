import json

import dateutil.parser
from django.contrib.gis.geos import Polygon
from django.db import transaction
from pyproj import CRS
import pystac
from pystac.extensions.eo import EOExtension
from pystac.extensions.projection import ProjectionExtension
from rest_framework import serializers
from rest_framework.reverse import reverse
from rgd.models import ChecksumFile, FileSourceType
from rgd.utility import get_or_create_no_commit
from rgd_imagery import models
from rgd_imagery.models.base import Image

from . import bands as band_utils
from ..utils import non_unique_get_or_create


class ItemSerializer(serializers.BaseSerializer):
    def _add_image_to_item(self, item, image, asset_type='image', roles=('data',)):
        asset = pystac.Asset(
            href=image.file.get_url(),
            title=image.file.name,
            roles=roles,
        )
        asset.set_owner(item)
        asset_eo_ext = EOExtension.ext(asset, add_if_missing=True)
        asset_eo_ext.bands = [
            band_utils.to_pystac(bandmeta)
            for bandmeta in image.bandmeta_set.filter(
                band_range__contained_by=(None, None),
            )
        ]
        item.add_asset(f'{asset_type}-{image.pk}', asset)

    def to_representation(self, instance: models.RasterMeta) -> dict:
        collection = instance.parent_raster.image_set.images.first().file.collection
        collection_id = collection and str(collection.pk) or 'default'
        item = pystac.Item(
            id=str(instance.pk),
            geometry=json.loads(instance.footprint.json),
            bbox=instance.extent,
            datetime=(instance.acquisition_date or instance.modified or instance.created),
            properties=dict(
                datetime=str(instance.acquisition_date),
                platform=(instance.instrumentation or 'unknown'),
                description=f'STAC Item {instance.pk}',
                title=(instance.parent_raster.name or f'STAC Item {instance.pk}'),
            ),
            collection=collection_id,
            href=reverse(
                'stac-collection-item',
                request=self.context.get('request'),
                args=[
                    collection_id,
                    str(instance.pk),
                ],
            ),
        )
        item.add_link(
            pystac.Link(
                'collection',
                reverse(
                    'stac-collection',
                    request=self.context.get('request'),
                    args=[collection_id],
                ),
                media_type='application/json',
            )
        )
        # 'proj' extension
        proj_ext = ProjectionExtension.ext(item, add_if_missing=True)
        proj_ext.apply(
            epsg=CRS.from_proj4(instance.crs).to_epsg(),
            transform=instance.transform,
        )
        # 'eo' extension
        item_eo_ext = EOExtension.ext(item, add_if_missing=True)
        item_eo_ext.cloud_cover = instance.cloud_cover
        # Add assets
        used_images = set()
        for image in (
            instance.parent_raster.image_set.images.exclude(pk__in=used_images)
            .select_related('file__collection')
            .all()
        ):
            used_images.add(image.pk)
            self._add_image_to_item(item, image, asset_type='image')
            for pim in image.processedimage_set.exclude(processed_image__in=used_images).all():
                self._add_image_to_item(
                    item,
                    pim.processed_image,
                    asset_type='processed-image',
                    roles=('processed-data',),
                )

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
        item_eo_ext = EOExtension.ext(item, add_if_missing=True)
        proj_ext = ProjectionExtension.ext(item, add_if_missing=True)
        image_ids, ancillary = [], []
        for asset in item.assets.values():
            checksum_file = non_unique_get_or_create(
                ChecksumFile,
                type=FileSourceType.URL,
                url=asset.href,
            )
            if len(item.assets) == 1 or (asset.roles and 'data' in asset.roles):
                image = non_unique_get_or_create(Image, file=checksum_file)
                image_ids.append(image.pk)
                for eo_band in item_eo_ext.bands:
                    bandmeta = band_utils.to_model(eo_band, image)
                    bandmeta.save()
            else:
                ancillary.append(checksum_file)

        image_set, _ = models.get_or_create_image_set(image_ids, defaults=dict(name=item.id))

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
            crs=f'+init=epsg:{proj_ext.epsg}',
            cloud_cover=item_eo_ext.cloud_cover,
            transform=proj_ext.transform,
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
