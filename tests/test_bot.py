import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from formatters import _format_button_text


def test_short_name_fits_without_truncation():
    result = {'name': 'Inception 1080p', 'seeds': '987', 'size': '12.1 GB'}
    text = _format_button_text(result)
    assert text == 'Inception 1080p · 987s · 12.1 GB'
    assert len(text.encode('utf-8')) <= 64


def test_name_over_30_bytes_is_truncated():
    result = {
        'name': 'Inception 2010 1080p BluRay x264-GROUP',  # 38 bytes
        'seeds': '120',
        'size': '14.2 GB',
    }
    text = _format_button_text(result)
    name_part = text.split(' · ')[0]
    assert len(name_part.encode('utf-8')) <= 30
    assert text.endswith('· 120s · 14.2 GB')


def test_truncated_name_ends_with_ellipsis():
    result = {
        'name': 'Very Long Movie Title That Cannot Possibly Fit',
        'seeds': '50',
        'size': '8.0 GB',
    }
    text = _format_button_text(result)
    assert '…' in text
    assert text.endswith('· 50s · 8.0 GB')


def test_multibyte_utf8_name_truncated_at_byte_boundary():
    result = {
        'name': 'Eredeti Magyar Cím Ékezetes Betűkkel ÁÉÍÓÖŐÚÜŰáéí',
        'seeds': '42',
        'size': '3.2 GB',
    }
    text = _format_button_text(result)
    name_part = text.split(' · ')[0].rstrip('…')
    assert len(name_part.encode('utf-8')) <= 30
    assert len(text.encode('utf-8')) <= 64
