import hashlib
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest

from infohash import compute_infohash


def _bencode(value):
    if isinstance(value, int):
        return f'i{value}e'.encode()
    if isinstance(value, bytes):
        return f'{len(value)}:'.encode() + value
    if isinstance(value, str):
        encoded = value.encode('utf-8')
        return f'{len(encoded)}:'.encode() + encoded
    if isinstance(value, list):
        return b'l' + b''.join(_bencode(item) for item in value) + b'e'
    if isinstance(value, dict):
        def key_bytes(item):
            key = item[0]
            return key.encode('utf-8') if isinstance(key, str) else key
        items = sorted(value.items(), key=key_bytes)
        return b'd' + b''.join(_bencode(k) + _bencode(v) for k, v in items) + b'e'
    raise TypeError(type(value))


def test_simple_single_file_torrent():
    info = b'd4:name4:test12:piece lengthi16384e6:pieces20:01234567890123456789e'
    expected = hashlib.sha1(info).hexdigest()
    torrent = b'd8:announce11:http://x/y/4:info' + info + b'e'
    assert compute_infohash(torrent) == expected


def test_multi_file_torrent_with_nested_lists():
    info = (
        b'd5:filesld6:lengthi100e4:pathl4:fileeed6:lengthi200e4:pathl5:file2eee'
        b'4:name3:dir12:piece lengthi16384e6:pieces20:01234567890123456789e'
    )
    expected = hashlib.sha1(info).hexdigest()
    torrent = b'd4:info' + info + b'13:creation datei1700000000ee'
    assert compute_infohash(torrent) == expected


def test_info_key_after_other_keys():
    info = b'd4:name4:abcd12:piece lengthi32768e6:pieces20:aaaaaaaaaaaaaaaaaaaae'
    expected = hashlib.sha1(info).hexdigest()
    torrent = b'd8:announce4:url:7:comment3:hi 4:info' + info + b'e'
    assert compute_infohash(torrent) == expected


def test_raises_on_non_dict():
    with pytest.raises(ValueError):
        compute_infohash(b'i42e')


def test_raises_when_info_missing():
    with pytest.raises(ValueError):
        compute_infohash(b'd8:announce4:url:e')


def test_realistic_torrent_with_utf8_and_nested_structure():
    info = {
        'files': [
            {'length': 1_234_567, 'path': ['Season 01', 'Eredeti Cím S01E01.mkv']},
            {'length': 7_654_321, 'path': ['Season 01', 'Eredeti Cím S01E02.mkv']},
            {'length': 4096, 'path': ['extras', 'sample.txt']},
        ],
        'name': 'Eredeti Magyar Sorozat ÁÉÍÓÖŐÚÜŰ',
        'piece length': 32768,
        'pieces': bytes(range(20)) * 12,
        'private': 1,
    }
    torrent = {
        'announce': 'https://tracker.example.com/announce',
        'announce-list': [
            ['https://tracker.example.com/announce'],
            ['https://backup.example.org/announce', 'udp://udp.example.net:6969'],
        ],
        'comment': 'test fixture',
        'created by': 'pytest',
        'creation date': 1700000000,
        'encoding': 'UTF-8',
        'info': info,
    }
    expected = hashlib.sha1(_bencode(info)).hexdigest()
    assert compute_infohash(_bencode(torrent)) == expected


def test_empty_pieces_and_zero_length_file():
    info = {
        'length': 0,
        'name': 'empty.bin',
        'piece length': 16384,
        'pieces': b'',
    }
    torrent = {'announce': 'http://x', 'info': info}
    expected = hashlib.sha1(_bencode(info)).hexdigest()
    assert compute_infohash(_bencode(torrent)) == expected
