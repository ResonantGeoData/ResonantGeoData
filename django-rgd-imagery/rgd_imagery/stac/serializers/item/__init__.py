import json

from pyproj import CRS
from pyproj.exceptions import CRSError
import pystac
from pystac.extensions.eo import EOExtension
from pystac.extensions.projection import ProjectionExtension
from rest_framework import serializers
from rest_framework.reverse import reverse
from rgd_imagery import models

from . import bands as band_utils


class ItemSerializer(serializers.BaseSerializer):
    def to_internal_value(self, data):
        return data

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
            for bandmeta in image.bandmeta_set.all()
            if bandmeta.band_range
        ]
        item.add_asset(f'{asset_type}-{image.pk}', asset)

    def to_representation(self, instance: models.RasterMeta) -> dict:
        item_images = instance.parent_raster.image_set.images.all()
        if item_images:
            collection = item_images[0].file.collection
        else:
            collection = None
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
        try:
            proj_ext = ProjectionExtension.ext(item, add_if_missing=True)
            proj_ext.apply(
                epsg=CRS.from_proj4(instance.crs).to_epsg(),
                transform=instance.transform,
            )
        except CRSError:
            pass
        # 'eo' extension
        item_eo_ext = EOExtension.ext(item, add_if_missing=True)
        item_eo_ext.cloud_cover = instance.cloud_cover
        # Add assets
        used_images = set()
        for image in item_images:
            if item not in used_images:
                used_images.add(image)
                self._add_image_to_item(item, image, asset_type='image')
                for pim in image.processedimage_set.all():
                    if pim.processed_image and pim.processed_image not in used_images:
                        used_images.add(pim.processed_image)
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
