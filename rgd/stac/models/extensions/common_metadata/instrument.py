from django.db import models

from rgd.stac.models.extensions import ExtendableModel, ModelExtension

"""
Adds metadata specifying a platform and instrument used in a data collection
mission.

These fields will often be combined with domain-specific extensions that
describe the actual data, such as the eo or sar extensions.

    `platform`: unique name of the specific platform the instrument is attached to.
    For satellites this would be the name of the satellite, whereas for drones this
    would be a unique name for the drone. Examples include landsat-8 (Landsat-8),
    sentinel-2a and sentinel-2b (Sentinel-2), terra and aqua (part of NASA EOS,
    carrying the MODIS instruments), mycorp-uav-034 (hypothetical drone name), and
    worldview02 (Maxar/DigitalGlobe WorldView-2).

    `instruments`: array of all the sensors used in the creation of the data. For
    example, data from the Landsat-8 platform is collected with the OLI sensor as
    well as the TIRS sensor, but the data is distributed together so would be
    specified as ['oli', 'tirs']. Other instrument examples include msi
    (Sentinel-2), aster (Terra), and modis (Terra and Aqua), c-sar (Sentinel-1) and
    asar (Envisat).

    `constellation`: The name of a logical collection of one or more platforms that
    have similar payloads and have their orbits arranged in a way to increase the
    temporal resolution of acquisitions of data with similar geometric and
    radiometric characteristics. This field allows users to search for related data
    sets without the need to specify which specific platform the data came from, for
    example, from either of the Sentinel-2 satellites. Examples include landsat-8
    (Landsat-8, a constellation consisting of a single platform), sentinel-2
    (Sentinel-2), rapideye (operated by Planet Labs), and modis (NASA EOS satellites
    Aqua and Terra). In the case of modis, this is technically referring to a pair
    of sensors on two different satellites, whose data is combined into a series of
    related products. Additionally, the Aqua satellite is technically part of the
    A-Train constellation and Terra is not part of a constellation, but these are
    combined to form the logical collection referred to as MODIS.

    `mission`: The name of the mission or campaign for collecting data. This could
    be a discrete set of data collections over a period of time (such as collecting
    drone imagery), or could be a set of tasks of related tasks from a satellite
    data collection.

    `gsd`: The nominal Ground Sample Distance for the data, as measured in meters on
    the ground. There are many definitions of GSD. The value of this field should be
    related to the spatial resolution at the sensor, rather than the pixel size of
    images after orthorectification, pansharpening, or scaling. The GSD of a sensor
    can vary depending on off-nadir and wavelength, so it is at the discretion of
    the implementer to decide which value most accurately represents the GSD. For
    example, Landsat8 optical and short-wave IR bands are all 30 meters, but the
    panchromatic band is 15 meters. The gsd should be 30 meters in this case because
    that is nominal spatial resolution at the sensor. The Planet PlanetScope Ortho
    Tile Product has an gsd of 3.7 (or 4 if rounding), even though the pixel size of
    the images is 3.125. For example, one might choose for WorldView-2 the
    Multispectral 20° off-nadir value of 2.07 and for WorldView-3 the Multispectral
    20° off-nadir value of 1.38.
"""


class InstrumentName(models.Model):
    name = models.TextField[str, str](unique=True)
    description = models.TextField[str, str]()


instrument = ModelExtension(
    title='Instrument Fields',
    identifier='schemas.stacspec.org/v1.0.0-rc.2/item-spec/json-schema/instrument.json',
    prefix='CommonInstrument',
)


def fields(model: ExtendableModel):
    return {
        'platform': models.TextField[str, str](
            help_text='Unique name of the specific platform to which the instrument is attached.',
            null=True,
        ),
        'instruments': models.ManyToManyField[InstrumentName, InstrumentName](
            InstrumentName,
            help_text='Name of instrument or sensor used (e.g., MODIS, ASTER, OLI, Canon F-1).',
        ),
        'constellation': models.TextField[str, str](
            help_text='Name of the constellation to which the platform belongs.',
            null=True,
        ),
        'mission': models.TextField[str, str](
            help_text='Name of the mission for which data is collected.',
            null=True,
        ),
        'gsd': models.FloatField[str, str](
            help_text='Ground Sample Distance at the sensor, in meters (m).',
            null=True,
        ),
    }


def opts(model: ExtendableModel):
    return {
        'constraints': [
            models.CheckConstraint(
                check=models.Q(gsd__gt=0),
                name='%(class)s_positive_gsd',
            )
        ]
    }


for model in ExtendableModel.get_children():
    instrument.extend_model(model=model, fields=fields(model), opts=opts(model))
