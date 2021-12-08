import inspect

import factory
from pytest_factoryboy import register
from rgd_testing_utils import factories
from rgd_testing_utils.api_fixtures import *  # noqa
from rgd_testing_utils.data_fixtures import *  # noqa

for _, fac in inspect.getmembers(factories):
    if inspect.isclass(fac) and issubclass(fac, factory.Factory):
        register(fac)
