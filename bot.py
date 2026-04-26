import asyncio
import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, filters, ContextTypes,
)
import config
import ncore
import qbittorrent

logging.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)

SELECTING = 0
SELECTING_CATEGORY = 1

def _allowed(update: Update) -> bool:
    return update.effective_user.id in config.ALLOWED_USERS


def _format_results(results: list) -> str:
    lines = []
    for i, result in enumerate(results, 1):
        name = result.get('name', 'Unknown')
        seeds = result.get('seeds', '?')
        size = result.get('size', '?')
        lines.append(f"{i}. {name}\n   Seeds: {seeds} · Size: {size}")
    return '\n\n'.join(lines)

def _format_size(size_bytes: int) -> str:
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"

def _state_en(state: str) -> str:
    return {
        'downloading': '⬇️ Downloading',
        'forcedDL':    '⬇️ Downloading',
        'stalledDL':   '⏸ Stalled',
        'queuedDL':    '🕐 Queued',
        'metaDL':      '🔍 Fetching metadata',
        'checkingDL':  '🔍 Checking',
        'checkingUP':  '🔍 Checking',
        'pausedDL':    '⏸ Paused',
        'seeding':     '✅ Done',
        'stalledUP':   '✅ Done',
        'uploading':   '✅ Done',
        'forcedUP':    '✅ Done',
        'pausedUP':    '✅ Done',
    }.get(state, f'❓ {state}')

async def dl_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _allowed(update):
        await update.message.reply_text("You don't have permission to use this bot.")
        return ConversationHandler.END

    args = list(context.args)
    categories = None
    if args and args[0] in ('-movie', '-series'):
        flag = args.pop(0)
        if flag == '-series':
            categories = config.CATEGORIES_SERIES

    query = ' '.join(args).strip()
    if not query:
        await update.message.reply_text(
            "Usage: /dl <title>\n"
            "Optional flag: /dl -movie <title> or /dl -series <title>"
        )
        return ConversationHandler.END

    label = " [series]" if categories == config.CATEGORIES_SERIES else ""
    await update.message.reply_text(f"Searching{label}: {query}...")

    try:
        results = ncore.search(query, config, categories=categories)
    except Exception as e:
        logging.exception("ncore search failed")
        await update.message.reply_text(f"Search error: {e}")
        return ConversationHandler.END

    if not results:
        await update.message.reply_text("No results found.")
        return ConversationHandler.END

    context.user_data['results'] = results
    list_text = _format_results(results)
    await update.message.reply_text(
        f"{list_text}\n\nWhich one should I download? (1-{len(results)})\n/cancel to abort"
    )
    return SELECTING


async def select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _allowed(update):
        return ConversationHandler.END

    results = context.user_data.get('results', [])
    try:
        choice = int(update.message.text.strip())
        if not 1 <= choice <= len(results):
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            f"Please enter a number between 1 and {len(results)}."
        )
        return SELECTING

    context.user_data['selected'] = results[choice - 1]
    await update.message.reply_text(
        f"Where should I save it?\n\n1. Movie ({config.QBIT_SAVE_PATH_MOVIES})\n2. Series ({config.QBIT_SAVE_PATH_SERIES})\n\n/cancel to abort"
    )
    return SELECTING_CATEGORY


async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _allowed(update):
        return ConversationHandler.END

    text = update.message.text.strip()
    if text == '1':
        save_path = config.QBIT_SAVE_PATH_MOVIES
        category = config.QBIT_CATEGORY_MOVIES
    elif text == '2':
        save_path = config.QBIT_SAVE_PATH_SERIES
        category = config.QBIT_CATEGORY_SERIES
    else:
        await update.message.reply_text("Please choose: 1 (Movie) or 2 (Series).")
        return SELECTING_CATEGORY

    torrent = context.user_data.get('selected')
    await update.message.reply_text(f"Starting download: {torrent['name']}...")

    try:
        hashes_before = qbittorrent.get_all_hashes(config)
        torrent_data = ncore.download_torrent(torrent['link'], config)
        qbittorrent.add_torrent(torrent_data, save_path, config, category)
    except Exception as e:
        logging.exception("download failed")
        await update.message.reply_text(f"Error: {e}")
        return ConversationHandler.END

    await asyncio.sleep(3)
    hashes_after = qbittorrent.get_all_hashes(config)
    new_hashes = hashes_after - hashes_before

    if new_hashes:
        torrent_hash = next(iter(new_hashes))
        context.application.bot_data.setdefault('tracking', {})[torrent_hash] = (
            update.effective_chat.id, torrent['name']
        )
        logging.info("Tracking torrent hash %s for chat %s", torrent_hash, update.effective_chat.id)
        await update.message.reply_text(f"Added: {torrent['name']}\nI'll notify you when it's done! 🔔")
    else:
        logging.warning("Could not find new torrent hash after adding")
        await update.message.reply_text(f"Added: {torrent['name']}")
    return ConversationHandler.END


async def check_downloads(context: ContextTypes.DEFAULT_TYPE):
    tracking = context.bot_data.get('tracking', {})
    if not tracking:
        return
    logging.info("Checking %d tracked torrent(s)", len(tracking))
    completed = []
    for torrent_hash, (chat_id, name) in tracking.items():
        try:
            progress = qbittorrent.get_torrent_progress(torrent_hash, config)
            logging.info("  %s -> progress: %s", name[:40], progress)
            if progress is not None and progress >= 1.0:
                await context.bot.send_message(chat_id=chat_id, text=f"✅ Download complete: {name}")
                completed.append(torrent_hash)
        except Exception:
            logging.exception("progress check failed for %s", torrent_hash)
    for torrent_hash in completed:
        del tracking[torrent_hash]


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Search cancelled.")
    return ConversationHandler.END


async def recent_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _allowed(update):
        await update.message.reply_text("You don't have permission to use this bot.")
        return

    try:
        torrents = qbittorrent.get_recent_torrents(config)
    except Exception as e:
        logging.exception("recent torrents failed")
        await update.message.reply_text(f"Error: {e}")
        return

    if not torrents:
        await update.message.reply_text("No torrents in the list.")
        return

    lines = []
    for i, torrent in enumerate(torrents, 1):
        name = torrent.get('name', '?')
        progress = int(torrent.get('progress', 0) * 100)
        size = _format_size(torrent.get('size', 0))
        state = _state_en(torrent.get('state', ''))
        status = f"✅ Done {progress}%" if progress == 100 else f"{state} {progress}%"
        lines.append(f"{i}. {status}\n📁 {name}\n💾 {size}")

    await update.message.reply_text('\n\n'.join(lines))


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name or "there"
    text = (
        f"Hey, {name}! 👋\n\n"
        "I'm an nCore torrent bot. I search nCore for movies and series "
        "and add them directly to qBittorrent - you just pick what you want.\n\n"
        "Here's how it works:\n\n"
        "1️⃣ Send a search:\n"
        "   /dl Inception\n"
        "   /dl -movie Inception  (movies only)\n"
        "   /dl -series Breaking Bad  (series only)\n\n"
        "2️⃣ Pick the best result (1-5):\n"
        "   Results are sorted by seeders, highest first.\n\n"
        "3️⃣ Choose where to save it:\n"
        "   1 = Movie  |  2 = Series\n\n"
        "4️⃣ Done! I'll notify you when the download finishes. ✅\n\n"
        "Other commands:\n"
        "/recent - Last 5 torrents and their status\n"
        "/cancel - Cancel current search\n"
        "/help - List all commands"
    )
    await update.message.reply_text(text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Available commands:\n\n"
        "/dl <title> - Search and download a torrent (HD movies + series)\n"
        "/dl -movie <title> - Search in movie categories only (hd_hun, hd)\n"
        "/dl -series <title> - Search in series categories only (hdser_hun, hdser)\n"
        "  1. Search for a movie or series\n"
        "  2. Pick from the results (1-5)\n"
        "  3. Choose the save location (Movie / Series)\n\n"
        "/cancel - Cancel an active search\n\n"
        "/recent - Last 5 added torrents and their status\n\n"
        "/myid - Show your Telegram user ID\n\n"
        "/help - This message"
    )
    await update.message.reply_text(text)


async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(f"Your Telegram ID: {uid}\nAdd it to ALLOWED_USERS in config.py.")


def main():
    app = Application.builder().token(config.TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('recent', recent_command))
    app.add_handler(CommandHandler('myid', myid_command))

    conv = ConversationHandler(
        entry_points=[CommandHandler('dl', dl_command)],
        states={
            SELECTING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, select_handler)
            ],
            SELECTING_CATEGORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, category_handler)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    app.add_handler(conv)
    app.job_queue.run_repeating(check_downloads, interval=60, first=10)
    logging.info("Bot started. Polling...")
    app.run_polling()

if __name__ == '__main__':
    main()
