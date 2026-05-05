NCORE_USERNAME = ""
NCORE_PASSHASH = ""     # get from browser: F12 -> Application -> Cookies -> ncore.pro -> pass

TELEGRAM_TOKEN = ""
ALLOWED_USERS = []      # Telegram user IDs, e.g. [123456789]

QBIT_URL = "http://192.168.1.x:8080"
QBIT_USERNAME = "admin"
QBIT_PASSWORD = ""
QBIT_SAVE_PATH_MOVIES = ""      # e.g. "F:\\Downloads\\Movies"
QBIT_SAVE_PATH_SERIES = ""      # e.g. "F:\\Downloads\\Series"
QBIT_CATEGORY_MOVIES = "Movies"
QBIT_CATEGORY_SERIES = "Series"

# Movie categories:
#   hd_hun      Movie HD/HU
#   hd          Movie HD/EN
#   dvd9_hun    Movie DVD9/HU
#   dvd9        Movie DVD9/EN
#   dvd_hun     Movie DVDR/HU
#   dvd         Movie DVDR/EN
#   xvid_hun    Movie SD/HU
#   xvid        Movie SD/EN
CATEGORIES = "hd_hun,hd"

# Series categories:
#   hdser_hun   Sorozat HD/HU
#   hdser       Sorozat HD/EN
#   dvdser_hun  Sorozat DVDR/HU
#   dvdser      Sorozat DVDR/EN
#   xvidser_hun Sorozat SD/HU
#   xvidser     Sorozat SD/EN
CATEGORIES_SERIES = "hdser_hun,hdser"
QUALITY_FILTER = []     # e.g. ["1080", "2160"] to only show those qualities, or [] for all
TOP_RESULTS = 5         # how many results to show in Telegram (after sorting by seeders)
MAX_PAGES = 5           # how many nCore search-result pages to fetch
