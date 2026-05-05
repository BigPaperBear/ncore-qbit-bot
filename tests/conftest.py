import importlib.util
import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, REPO_ROOT)

try:
    import config
except ModuleNotFoundError:
    spec = importlib.util.spec_from_file_location(
        'config', os.path.join(REPO_ROOT, 'config.example.py')
    )
    config_module = importlib.util.module_from_spec(spec)
    sys.modules['config'] = config_module
    spec.loader.exec_module(config_module)

import ncore
import qbittorrent


@pytest.fixture(autouse=True)
def reset_module_globals():
    qbittorrent._session_cache = None
    ncore._default_client = None
    yield
    qbittorrent._session_cache = None
    ncore._default_client = None
