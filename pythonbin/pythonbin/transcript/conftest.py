import pytest
from .config import Config


@pytest.fixture
def example_config():
    """An example fixture that provides a Config object."""
    return Config(polling_interval=5)
