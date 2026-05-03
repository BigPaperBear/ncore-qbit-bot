import requests

_session_cache = None


def _session(config):
    global _session_cache
    if _session_cache is None:
        s = requests.Session()
        s.post(
            f"{config.QBIT_URL}/api/v2/auth/login",
            data={'username': config.QBIT_USERNAME, 'password': config.QBIT_PASSWORD},
        ).raise_for_status()
        _session_cache = s
    return _session_cache


def _request(config, method, url, **kwargs):
    global _session_cache
    resp = getattr(_session(config), method.lower())(url, **kwargs)
    if resp.status_code == 403:
        _session_cache = None
        resp = getattr(_session(config), method.lower())(url, **kwargs)
    resp.raise_for_status()
    return resp


def add_torrent(torrent_data: bytes, save_path: str, config, category: str = '') -> str:
    resp = _request(
        config, 'POST', f"{config.QBIT_URL}/api/v2/torrents/add",
        files={'torrents': ('torrent.torrent', torrent_data, 'application/x-bittorrent')},
        data={k: v for k, v in {'savepath': save_path, 'category': category}.items() if v},
    )
    return resp.text


def get_torrent_progress(torrent_hash: str, config):
    torrents = _request(
        config, 'GET', f"{config.QBIT_URL}/api/v2/torrents/info",
        params={'hashes': torrent_hash},
    ).json()
    return torrents[0]['progress'] if torrents else None


def get_recent_torrents(config, count=5):
    torrents = _request(config, 'GET', f"{config.QBIT_URL}/api/v2/torrents/info").json()
    torrents.sort(key=lambda t: t.get('added_on', 0), reverse=True)
    return torrents[:count]
