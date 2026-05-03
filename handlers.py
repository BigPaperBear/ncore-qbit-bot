import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, ContextTypes

import config
import ncore
import qbittorrent
from formatters import _format_button_text, _format_size, _state_label
from infohash import compute_infohash

SELECTING_TYPE = 0
SELECTING_RESULT = 1

MAX_MISSING_CHECKS = 10


async def dl_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = ' '.join(context.args).strip()
    if not query:
        await update.message.reply_text("Usage: /dl <title>")
        return ConversationHandler.END

    context.user_data['query'] = query
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton('🎬 Movie', callback_data='type:movie'),
        InlineKeyboardButton('📺 Series', callback_data='type:series'),
    ]])
    await update.message.reply_text(f'"{query}" — movie or series?', reply_markup=keyboard)
    return SELECTING_TYPE


async def type_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    callback = update.callback_query
    await callback.answer()

    is_series = callback.data == 'type:series'
    context.user_data['save_path'] = config.QBIT_SAVE_PATH_SERIES if is_series else config.QBIT_SAVE_PATH_MOVIES
    context.user_data['category'] = config.QBIT_CATEGORY_SERIES if is_series else config.QBIT_CATEGORY_MOVIES
    categories = config.CATEGORIES_SERIES if is_series else config.CATEGORIES

    search_query = context.user_data['query']
    await callback.edit_message_text(f'Searching: {search_query}...')

    try:
        results = ncore.search(search_query, config, categories=categories)
    except Exception as e:
        logging.exception("ncore search failed")
        await callback.edit_message_text(f'Search error: {e}')
        return ConversationHandler.END

    if not results:
        await callback.edit_message_text('No results found.')
        return ConversationHandler.END

    context.user_data['results'] = results
    buttons = [[InlineKeyboardButton(_format_button_text(torrent), callback_data=f'result:{i}')]
               for i, torrent in enumerate(results)]
    buttons.append([InlineKeyboardButton('❌ Cancel', callback_data='action:cancel')])
    await callback.edit_message_text('Choose one:', reply_markup=InlineKeyboardMarkup(buttons))
    return SELECTING_RESULT


async def result_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    callback = update.callback_query
    await callback.answer()

    result_index = int(callback.data.split(':')[1])
    results = context.user_data.get('results', [])
    torrent = results[result_index]
    save_path = context.user_data['save_path']
    category = context.user_data['category']

    await callback.edit_message_text(f'Starting download: {torrent["name"]}...')

    try:
        torrent_data = ncore.download_torrent(torrent['link'], config)
        torrent_hash = compute_infohash(torrent_data)
        qbittorrent.add_torrent(torrent_data, save_path, config, category)
    except Exception as e:
        logging.exception("download failed")
        await callback.edit_message_text(f'Error: {e}')
        return ConversationHandler.END

    context.application.bot_data.setdefault('tracking', {})[torrent_hash] = {
        'chat_id': update.effective_chat.id,
        'name': torrent['name'],
        'missing': 0,
    }
    logging.info("Tracking torrent hash %s for chat %s", torrent_hash, update.effective_chat.id)
    await callback.edit_message_text(f"Added: {torrent['name']}\nI'll notify you when it's done! 🔔")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Search cancelled.")
    return ConversationHandler.END


async def cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    callback = update.callback_query
    await callback.answer()
    await callback.edit_message_text("Search cancelled.")
    return ConversationHandler.END


async def check_downloads(context: ContextTypes.DEFAULT_TYPE):
    tracking = context.bot_data.get('tracking', {})
    if not tracking:
        return
    logging.info("Checking %d tracked torrent(s)", len(tracking))
    finished = []
    for torrent_hash, entry in tracking.items():
        try:
            progress = qbittorrent.get_torrent_progress(torrent_hash, config)
            logging.info("  %s -> progress: %s", entry['name'][:40], progress)
            if progress is None:
                entry['missing'] += 1
                if entry['missing'] >= MAX_MISSING_CHECKS:
                    logging.warning("Dropping %s: missing from qBit for %d checks",
                                    entry['name'], entry['missing'])
                    finished.append(torrent_hash)
                continue
            entry['missing'] = 0
            if progress >= 1.0:
                await context.bot.send_message(chat_id=entry['chat_id'],
                                               text=f"✅ Download complete: {entry['name']}")
                finished.append(torrent_hash)
        except Exception:
            logging.exception("progress check failed for %s", torrent_hash)
    for torrent_hash in finished:
        del tracking[torrent_hash]


async def recent_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        state = _state_label(torrent.get('state', ''))
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
        "   /dl Inception\n\n"
        "2️⃣ Pick Movie or Series\n\n"
        "3️⃣ Tap the result you want\n\n"
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
        "/dl <title> - Search and download a torrent\n"
        "  1. Pick Movie or Series\n"
        "  2. Tap the result you want\n\n"
        "/cancel - Cancel an active search\n\n"
        "/recent - Last 5 added torrents and their status\n\n"
        "/myid - Show your Telegram user ID\n\n"
        "/help - This message"
    )
    await update.message.reply_text(text)


async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(f"Your Telegram ID: {uid}\nAdd it to ALLOWED_USERS in config.py.")
