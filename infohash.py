import hashlib


def _scan_value(data: bytes, pos: int) -> int:
    """Return the index just past the bencoded value starting at pos."""
    marker = data[pos:pos+1]
    if marker == b'i':
        return data.index(b'e', pos) + 1
    if marker == b'l' or marker == b'd':
        pos += 1
        while data[pos:pos+1] != b'e':
            pos = _scan_value(data, pos)
        return pos + 1
    if marker.isdigit():
        colon = data.index(b':', pos)
        length = int(data[pos:colon])
        return colon + 1 + length
    raise ValueError(f"unexpected byte at offset {pos}: {marker!r}")


def compute_infohash(torrent_bytes: bytes) -> str:
    """Lowercase SHA-1 hex of the bencoded info dict (BitTorrent v1 infohash)."""
    if torrent_bytes[:1] != b'd':
        raise ValueError("not a bencoded dict")
    pos = 1
    while torrent_bytes[pos:pos+1] != b'e':
        colon = torrent_bytes.index(b':', pos)
        key_len = int(torrent_bytes[pos:colon])
        key_start = colon + 1
        value_start = key_start + key_len
        key = torrent_bytes[key_start:value_start]
        value_end = _scan_value(torrent_bytes, value_start)
        if key == b'info':
            return hashlib.sha1(torrent_bytes[value_start:value_end]).hexdigest()
        pos = value_end
    raise ValueError("info dict not found")
