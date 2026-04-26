import requests


def _session(config):
    session = requests.Session()
    session.post(
        f"{config.QBIT_URL}/api/v2/auth/login",
        data={'username': config.QBIT_USERNAME, 'password': config.QBIT_PASSWORD},
    ).raise_for_status()
    return session


def add_torrent(torrent_data: bytes, save_path: str, config, category: str = '') -> str:
    session = _session(config)

    resp = session.post(
        f"{config.QBIT_URL}/api/v2/torrents/add",
        files={'torrents': ('torrent.torrent', torrent_data, 'application/x-bittorrent')},
        data={k: v for k, v in {'savepath': save_path, 'category': category}.items() if v},
    )
    resp.raise_for_status()
    return resp.text


def get_all_hashes(config) -> set:
    torrents = _session(config).get(f"{config.QBIT_URL}/api/v2/torrents/info").json()
    return {t['hash'] for t in torrents}


def get_torrent_progress(torrent_hash: str, config):
    torrents = _session(config).get(
        f"{config.QBIT_URL}/api/v2/torrents/info",
        params={'hashes': torrent_hash},
    ).json()
    return torrents[0]['progress'] if torrents else None


def get_recent_torrents(config, count=5):
    torrents = _session(config).get(f"{config.QBIT_URL}/api/v2/torrents/info").json()
    torrents.sort(key=lambda t: t.get('added_on', 0), reverse=True)
    return torrents[:count]
