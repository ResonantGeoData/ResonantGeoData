import inspect

import factory
from pytest_factoryboy import register
from rgd_testing_utils import factories as tfactories
from rgd_testing_utils.api_fixtures import *  # noqa
from rgd_testing_utils.data_fixtures import *  # noqa

from . import factories

for _, fac in inspect.getmembers(tfactories):
    if inspect.isclass(fac) and issubclass(fac, factory.Factory):
        register(fac)

for _, fac in inspect.getmembers(factories):
    if inspect.isclass(fac) and issubclass(fac, factory.Factory):
        register(fac)
