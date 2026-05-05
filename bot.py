import logging
from pathlib import Path

from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ConversationHandler,
    PicklePersistence, filters,
)

import config
from handlers import (
    SELECTING_TYPE, SELECTING_RESULT,
    dl_command, type_handler, result_handler,
    cancel, cancel_callback, ensure_check_job,
    recent_command, start_command, help_command, myid_command,
)

logging.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)


async def post_init(app):
    if app.bot_data.get('tracking'):
        ensure_check_job(app)
        logging.info("Resuming tracking for %d torrent(s)", len(app.bot_data['tracking']))


def main():
    Path("data").mkdir(exist_ok=True)
    persistence = PicklePersistence(filepath="data/bot_data.pickle")
    app = (
        Application.builder()
        .token(config.TELEGRAM_TOKEN)
        .persistence(persistence)
        .post_init(post_init)
        .build()
    )

    allowed = filters.User(user_id=config.ALLOWED_USERS)

    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('recent', recent_command, filters=allowed))
    app.add_handler(CommandHandler('myid', myid_command))

    conv = ConversationHandler(
        entry_points=[CommandHandler('dl', dl_command, filters=allowed)],
        states={
            SELECTING_TYPE: [
                CallbackQueryHandler(type_handler, pattern='^type:'),
            ],
            SELECTING_RESULT: [
                CallbackQueryHandler(result_handler, pattern='^result:'),
                CallbackQueryHandler(cancel_callback, pattern='^action:cancel$'),
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        conversation_timeout=300,
    )
    app.add_handler(conv)
    logging.info("Bot started. Polling...")
    app.run_polling()


if __name__ == '__main__':
    main()
