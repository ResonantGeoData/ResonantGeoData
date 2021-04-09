from pathlib import Path
import re

import pkg_resources
import pytest

RGDC_VERSION_REGEX = r'__version__ = \'(.*)\''


@pytest.fixture
def rgdc_version():
    base_dir = Path(__file__).parent.parent.parent.parent
    version_file = base_dir / 'rgdc' / 'rgdc' / 'version.py'

    with open(version_file) as file_in:
        file_content = file_in.read()
        version = re.search(RGDC_VERSION_REGEX, file_content)

    return version.group(1)


def test_client_version_match(rgdc_version):
    rgd_version = next(
        pkg.version for pkg in pkg_resources.working_set if pkg.key == 'resonantgeodata'
    )

    assert rgd_version == rgdc_version
