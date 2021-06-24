from pkg_resources import DistributionNotFound, get_distribution

from .rgdc import Rgdc  # noqa F401

try:
    __version__ = get_distribution('rgd-client').version
except DistributionNotFound:
    # package is not installed
    __version__ = None
