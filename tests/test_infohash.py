import hashlib
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest

from infohash import compute_infohash


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
