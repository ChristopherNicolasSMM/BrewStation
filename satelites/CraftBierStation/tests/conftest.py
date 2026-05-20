import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.fixtures.mock_gpio import cleanup


@pytest.fixture(autouse=True)
def auto_cleanup():
    cleanup()
    yield

@pytest.fixture
def config_path():
    return os.path.join(os.path.dirname(__file__), 'fixtures', 'test_config.conf')
