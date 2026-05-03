import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import ncore
import qbittorrent


@pytest.fixture(autouse=True)
def reset_module_globals():
    qbittorrent._session_cache = None
    ncore._default_client = None
    yield
    qbittorrent._session_cache = None
    ncore._default_client = None
