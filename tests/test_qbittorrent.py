import os
import sys
from unittest.mock import patch, MagicMock
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import qbittorrent


def setup_function():
    qbittorrent._session_cache = None


class FakeConfig:
    QBIT_URL = 'http://localhost:8080'
    QBIT_USERNAME = 'admin'
    QBIT_PASSWORD = 'testpass'


def test_add_torrent_logs_in_and_posts():
    fake_session = MagicMock()
    fake_session.post.return_value.text = 'Ok.'
    fake_session.post.return_value.raise_for_status = MagicMock()

    with patch('qbittorrent.requests.Session', return_value=fake_session):
        result = qbittorrent.add_torrent(b'fake torrent data', '/downloads/movies', FakeConfig(), 'Movies')

    assert result == 'Ok.'
    calls = [str(c) for c in fake_session.post.call_args_list]
    assert any('auth/login' in c for c in calls)
    assert any('torrents/add' in c for c in calls)


def test_add_torrent_raises_on_login_failure():
    fake_session = MagicMock()
    fake_session.post.return_value.raise_for_status.side_effect = Exception('401')

    with patch('qbittorrent.requests.Session', return_value=fake_session):
        try:
            qbittorrent.add_torrent(b'data', '/downloads', FakeConfig(), '')
            assert False, "Should have raised"
        except Exception:
            pass
