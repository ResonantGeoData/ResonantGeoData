import decimal
from decimal import Decimal
import json

from bidict import bidict
import dateutil.parser
from django.contrib.gis.geos import Polygon
from django.db import transaction
from pyproj import CRS
import pystac
from rest_framework import serializers
from rgd.models import ChecksumFile, FileSourceType
from rgd.utility import get_or_create_no_commit

from .. import models

BAND_RANGE_BY_COMMON_NAMES = bidict(
    {
        'coastal': (Decimal(0.40), Decimal(0.45)),
        'blue': (Decimal(0.45), Decimal(0.50)),
        'green': (Decimal(0.50), Decimal(0.60)),
        'red': (Decimal(0.60), Decimal(0.70)),
        'yellow': (Decimal(0.58), Decimal(0.62)),
        'pan': (Decimal(0.50), Decimal(0.70)),
        'rededge': (Decimal(0.70), Decimal(0.79)),
        'nir': (Decimal(0.75), Decimal(1.00)),
        'nir08': (Decimal(0.75), Decimal(0.90)),
        'nir09': (Decimal(0.85), Decimal(1.05)),
        'cirrus': (Decimal(1.35), Decimal(1.40)),
        'swir16': (Decimal(1.55), Decimal(1.75)),
        'swir22': (Decimal(2.10), Decimal(2.30)),
        'lwir': (Decimal(10.5), Decimal(12.5)),
        'lwir11': (Decimal(10.5), Decimal(11.5)),
        'lwir12': (Decimal(11.5), Decimal(12.5)),
    }
)


class STACRasterSerializer(serializers.BaseSerializer):
    def to_internal_value(self, data):
        # item = pystac.Item.from_dict(data)
        # errors = item.validate()
        # if errors:
        #     raise serializers.ValidationError(errors)
        return data

    def _add_image_to_item(self, item, image, asset_type='image', roles=('data',)):
        if image.file.type != FileSourceType.URL:
            # TODO: we need fix this
            raise ValueError('Files must point to valid URL resources, not internal storage.')
        bands = []
        for bandmeta in image.bandmeta_set.filter(band_range__contained_by=(None, None)):
            band = pystac.extensions.eo.Band.create(
                name=f'B{bandmeta.band_number}',
                description=bandmeta.description,
            )
            # The wavelength statistics is described by either the
            # common_name or via center_wavelength and full_width_half_max.
            # We can derive our bandmeta.band_range.lower,
            # bandmeta.band_range.upper from the center_wavelength
            # and full_width_half_max.
            if (
                bandmeta.band_range.lower,
                bandmeta.band_range.upper,
            ) in BAND_RANGE_BY_COMMON_NAMES.inverse:
                band.common_name = BAND_RANGE_BY_COMMON_NAMES.inverse[
                    (bandmeta.band_range.lower, bandmeta.band_range.upper)
                ]
            else:
                with decimal.localcontext(decimal.BasicContext):
                    band.center_wavelength = float(
                        (bandmeta.band_range.lower + bandmeta.band_range.upper) / 2
                    )
                    band.full_width_half_max = float(
                        bandmeta.band_range.upper - bandmeta.band_range.lower
                    )

            bands.append(band)
        asset = pystac.Asset(
            href=image.file.get_url(),
            title=image.file.name,
            roles=roles,
        )
        item.add_asset(f'{asset_type}-{image.pk}', asset)
        item.ext.eo.set_bands(
            bands=bands
            or [
                pystac.extensions.eo.Band.create(
                    name=image.file.name,
                    description=image.bandmeta_set.first().description,
                )
            ],
            asset=asset,
        )

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
        used_images = set()
        for image in instance.parent_raster.image_set.images.all():
            if image.id in used_images:
                continue
            used_images.add(image.id)
            self._add_image_to_item(item, image, asset_type='image')
            for pim in image.processedimage_set.all():
                if pim.processed_image.id in used_images:
                    continue
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
        image_ids, ancillary = [], []
        for name in item.assets:
            asset = item.assets[name]
            checksum_file, _ = ChecksumFile.objects.get_or_create(
                type=FileSourceType.URL,
                url=asset.href,
            )
            if len(item.assets) == 1 or (asset.roles and 'data' in asset.roles):
                image, _ = models.Image.objects.get_or_create(file=checksum_file)
                image_ids.append(image.pk)
                for eo_band in item.ext.eo.bands:
                    if eo_band.name.startswith('B') and eo_band.name[1:].isdigit():
                        eo_band_number = int(eo_band.name[1:])
                    else:
                        eo_band_number = 0  # TODO: confirm reasonable default here
                    if eo_band.common_name in BAND_RANGE_BY_COMMON_NAMES:
                        eo_band_spectral_lower, eo_band_spectral_upper = BAND_RANGE_BY_COMMON_NAMES[
                            eo_band.common_name
                        ]
                    elif eo_band.center_wavelength and eo_band.full_width_half_max:
                        eo_band_spectral_lower = (
                            eo_band.eo_band_spectral_upper - eo_band.full_width_half_max / 2
                        )
                        eo_band_spectral_upper = (
                            eo_band.center_wavelength + eo_band.full_width_half_max / 2
                        )
                    bandmeta = models.BandMeta.objects.get_or_create(
                        parent_image=image,
                        band_number=eo_band_number,
                    )
                    bandmeta.description = eo_band.description
                    bandmeta.band_range = (
                        Decimal(eo_band_spectral_lower),
                        Decimal(eo_band_spectral_upper),
                    )
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
