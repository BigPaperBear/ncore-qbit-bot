from urllib.parse import urlparse, parse_qs, quote_plus
from urllib.request import build_opener, HTTPCookieProcessor
from html.parser import HTMLParser
from http.cookiejar import CookieJar

BASE_URL = 'https://ncore.pro'


class NCoreParser(HTMLParser):

    def __init__(self, url):
        super().__init__()
        self.url = url
        self.key = None
        self.next_field = None
        self.torrent = None
        self.results = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        cls = attrs.get('class', '')

        if tag == 'link' and 'href' in attrs:
            qs = parse_qs(urlparse(attrs['href']).query)
            if qs.get('key'):
                self.key = qs['key'][0]

        if tag == 'div' and cls == 'box_torrent':
            self.torrent = {}

        if self.torrent is None:
            return

        if tag == 'a':
            link = attrs.get('href', '')
            if 'title' in attrs:
                self.torrent['name'] = attrs['title']
                self.torrent['desc_link'] = f"{self.url}/{link}"
                dl_link = link.replace('details', 'download') + '&key=' + (self.key or '')
                self.torrent['link'] = f"{self.url}/{dl_link}"
            elif 'peers' in link:
                self.next_field = 'seeds' if 'seeds' not in self.torrent else 'leech'
        elif tag == 'div' and cls:
            if cls.startswith('box_meret'):
                self.next_field = 'size'
            elif cls.startswith('box_feltolto'):
                self._finalize()

    def handle_data(self, data):
        if self.next_field:
            self.torrent[self.next_field] = data.strip()
            self.next_field = None

    def _finalize(self):
        if self.torrent and 'name' in self.torrent:
            self.results.append(self.torrent)
        self.torrent = None


def _filter_and_sort(results, quality, top_n):
    if quality:
        results = [r for r in results if any(q.lower() in r.get('name', '').lower() for q in quality)]

    def seed_key(r):
        try:
            return int(str(r.get('seeds', '0')).strip().lstrip('+'))
        except (ValueError, TypeError):
            return 0

    return sorted(results, key=seed_key, reverse=True)[:top_n]


class NCoreClient:
    def __init__(self, config, opener=None):
        self.config = config
        self.opener = opener

    def _login(self):
        passhash = getattr(self.config, 'NCORE_PASSHASH', '')
        if not passhash:
            raise RuntimeError(
                "NCORE_PASSHASH is required — nCore uses reCAPTCHA so username/password login is not possible. "
                "Get your 'pass' cookie value from nCore and set NCORE_PASSHASH in config.py."
            )

        cookie = f"nyelv=hu; stilus=brutecore; nick={self.config.NCORE_USERNAME}; pass={passhash}"
        jar = CookieJar()
        opener = build_opener(HTTPCookieProcessor(jar))
        opener.addheaders = [('User-agent', 'Mozilla/5.0'), ('cookie', cookie)]
        resp = opener.open(BASE_URL + '/index.php')
        if 'login.php' in resp.geturl():
            raise RuntimeError(
                "ncore login failed — NCORE_PASSHASH is invalid or expired, update it in config.py"
            )
        return opener

    def _ensure_opener(self):
        if self.opener is None:
            self.opener = self._login()
        return self.opener

    def reset(self):
        self.opener = None

    def search(self, query, categories=None):
        cats = categories or self.config.CATEGORIES
        for attempt in range(2):
            try:
                opener = self._ensure_opener()
                all_results = []
                for page in range(1, self.config.MAX_PAGES + 1):
                    url = (
                        f"{BASE_URL}/torrents.php?miszerint=seeders&hogyan=DESC"
                        f"&tipus=kivalasztottak_kozott&mire={quote_plus(query)}"
                        f"&kivalasztott_tipus={cats}&oldal={page}"
                    )
                    resp = opener.open(url)
                    html = resp.read().decode('utf-8')

                    parser = NCoreParser(BASE_URL)
                    parser.feed(html)
                    parser.close()

                    if not parser.results:
                        break
                    all_results.extend(parser.results)

                return _filter_and_sort(all_results, self.config.QUALITY_FILTER, self.config.TOP_RESULTS)
            except Exception:
                if attempt == 0:
                    self.reset()
                else:
                    raise

    def download_torrent(self, link):
        for attempt in range(2):
            try:
                opener = self._ensure_opener()
                return opener.open(link).read()
            except Exception:
                if attempt == 0:
                    self.reset()
                else:
                    raise


_default_client = None


def _client(config):
    global _default_client
    if _default_client is None:
        _default_client = NCoreClient(config)
    return _default_client


def search(query, config, categories=None):
    return _client(config).search(query, categories=categories)


def download_torrent(link, config):
    return _client(config).download_torrent(link)
