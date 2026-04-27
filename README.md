# nCore Telegram Bot

A Telegram bot that searches nCore and adds torrents to qBittorrent from your phone.

---

## How it works

1. Send `/dl <title>` in Telegram
2. Choose Movie or Series
3. Tap the result you want (sorted by seeders)
4. The bot adds it to qBittorrent and notifies you when it's done

---

## Requirements

- Docker and Docker Compose
- qBittorrent running with Web UI enabled
- An nCore account
- A Telegram bot token (get one from [@BotFather](https://t.me/BotFather))

---

## Setup

### 1. Clone the project

```bash
git clone <repo-url>
cd ncore-bot
```

### 2. Create your config file

```bash
cp config.example.py config.py
```

Open `config.py` and fill in your details:

```python
# nCore
NCORE_USERNAME = "your_username"
NCORE_PASSHASH = "your_pass_cookie_value"

# Telegram
TELEGRAM_TOKEN = "your_token_from_botfather"
ALLOWED_USERS = [123456789]   # your Telegram user ID

# qBittorrent
QBIT_URL = "http://192.168.1.x:8080"
QBIT_USERNAME = "admin"
QBIT_PASSWORD = "your_password"
QBIT_SAVE_PATH_MOVIES = "F:\\Downloads\\Movies"
QBIT_SAVE_PATH_SERIES = "F:\\Downloads\\Series"
QBIT_CATEGORY_MOVIES = "Movies"
QBIT_CATEGORY_SERIES = "Series"

# Search
CATEGORIES = "hd_hun,hd"
CATEGORIES_SERIES = "hdser_hun,hdser"
QUALITY_FILTER = ""     # e.g. "1080" to only show 1080p results, or "" for all
TOP_RESULTS = 5
```

**How to find your Telegram user ID:** Start the bot, send `/myid`, and it will reply with your ID. Add that number to `ALLOWED_USERS`.

**How to get NCORE_PASSHASH:**

nCore uses reCAPTCHA on the login page, so the bot cannot log in with a username and password directly. Instead it uses a cookie called `pass` that your browser stores after you log in. Follow these steps to get it:

1. Log out of nCore in your browser
2. Log back in, but before clicking the login button, check the "Csökkentett biztonság" (Reduced security) checkbox. This tells nCore to store your session in a long-lived cookie. If you already had this checked last time you logged in, you can skip the logout and just read the cookie value directly.
3. After logging in, open the browser developer tools (F12)
4. Go to Application -> Cookies -> ncore.pro
5. Find the cookie named `pass` and copy its value
6. Paste that value into `NCORE_PASSHASH` in `config.py`

You can log out and back in normally after this. The cookie value stays valid for a long time. If the bot ever stops working with a login error, just repeat these steps to get a fresh value.

### 3. Start the bot

```bash
docker-compose up -d --build
```

The bot will start and automatically restart if the machine reboots.

**View logs:**
```bash
docker-compose logs -f
```

**Stop the bot:**
```bash
docker-compose down
```

**Restart after changing config.py:**
```bash
docker-compose up -d --build
```

---

## Commands

| Command | What it does |
|---|---|
| `/dl <title>` | Search nCore and download |
| `/recent` | Show the last 5 torrents and their status |
| `/myid` | Show your Telegram user ID |
| `/start` | Show how to use the bot |
| `/help` | List all commands |
| `/cancel` | Cancel the current search |

---

## Example

```
You:  /dl Breaking Bad

Bot:  "Breaking Bad" — movie or series?
      [ Movie ]  [ Series ]

You:  Series

Bot:  Choose one:
      [ Breaking Bad S01 1080p HUN · 42s · 28.5 GB ]
      [ Breaking Bad S01 720p HUN  · 18s · 12.1 GB ]
      [ Cancel ]

You:  Breaking Bad S01 1080p HUN · 42s · 28.5 GB

Bot:  Starting download: Breaking Bad S01 1080p HUN...

      ... later ...

Bot:  Download complete: Breaking Bad S01 1080p HUN
```

---

## Adding more users

Add more Telegram user IDs to `ALLOWED_USERS` in `config.py`:

```python
ALLOWED_USERS = [123456789, 987654321]
```

Each person only gets a notification for their own downloads.

---

## Troubleshooting

**No results found**
- Check if `QUALITY_FILTER` in `config.py` is too strict. Set it to `""` to turn it off.

**SSL or connection error**
- The bot retries automatically with a fresh login. If it still fails, check your network connection and whether nCore is accessible in your browser.

**"You don't have permission to use this bot"**
- Your Telegram user ID is missing from `ALLOWED_USERS`. Send `/myid` to get your ID, add it to `config.py`, then run `docker-compose up -d --build`.

**No notification when download finishes**
- Run `docker-compose logs -f` and look for lines with `Checking N tracked torrent(s)` to see if the bot is checking progress.
- The bot checks every 60 seconds and sends the message as soon as progress hits 100%.
