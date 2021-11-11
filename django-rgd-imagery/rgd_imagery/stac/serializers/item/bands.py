import decimal
from decimal import Decimal

from bidict import bidict
from pystac.extensions.eo import Band
from rgd_imagery import models

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


def to_pystac(bandmeta: models.BandMeta):
    band = Band.create(
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
            band.full_width_half_max = float(bandmeta.band_range.upper - bandmeta.band_range.lower)
    return band
