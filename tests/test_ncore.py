import os

from ncore import NCoreParser, _filter_and_sort

FIXTURE = os.path.join(os.path.dirname(__file__), 'fixtures', 'ncore_results.html')


def _load_fixture():
    with open(FIXTURE, encoding='utf-8') as f:
        return f.read()


def test_parser_extracts_two_torrents():
    html = _load_fixture()
    parser = NCoreParser('https://ncore.pro')
    parser.feed(html)
    assert len(parser.results) == 2


def test_parser_extracts_name():
    html = _load_fixture()
    parser = NCoreParser('https://ncore.pro')
    parser.feed(html)
    assert parser.results[0]['name'] == 'Inception 2010 1080p BluRay x264'


def test_parser_builds_download_link():
    html = _load_fixture()
    parser = NCoreParser('https://ncore.pro')
    parser.feed(html)
    link = parser.results[0]['link']
    assert 'download' in link
    assert 'testkey123' in link


def test_parser_extracts_seeds():
    html = _load_fixture()
    parser = NCoreParser('https://ncore.pro')
    parser.feed(html)
    assert parser.results[0]['seeds'] == '120'


def test_parser_extracts_size():
    html = _load_fixture()
    parser = NCoreParser('https://ncore.pro')
    parser.feed(html)
    assert parser.results[0]['size'] == '14.2 GB'


def test_filter_keeps_1080p_only():
    results = [
        {'name': 'Inception 2010 1080p BluRay', 'seeds': '100', 'size': '10 GB', 'link': 'a'},
        {'name': 'Inception 2010 720p BluRay', 'seeds': '200', 'size': '5 GB', 'link': 'b'},
    ]
    filtered = _filter_and_sort(results, quality=['1080'], top_n=5)
    assert len(filtered) == 1
    assert '1080p' in filtered[0]['name']


def test_filter_sorts_by_seeds_descending():
    results = [
        {'name': 'Movie A 1080p', 'seeds': '10', 'size': '5 GB', 'link': 'a'},
        {'name': 'Movie B 1080p', 'seeds': '200', 'size': '8 GB', 'link': 'b'},
        {'name': 'Movie C 1080p', 'seeds': '50', 'size': '6 GB', 'link': 'c'},
    ]
    filtered = _filter_and_sort(results, quality=['1080'], top_n=5)
    assert filtered[0]['seeds'] == '200'
    assert filtered[1]['seeds'] == '50'


def test_filter_respects_top_n():
    results = [
        {'name': f'Movie {i} 1080p', 'seeds': str(i), 'size': '5 GB', 'link': str(i)}
        for i in range(10)
    ]
    filtered = _filter_and_sort(results, quality=['1080'], top_n=3)
    assert len(filtered) == 3
