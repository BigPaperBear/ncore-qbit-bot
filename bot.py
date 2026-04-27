import logging

from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler

import config
from handlers import (
    SELECTING_TYPE, SELECTING_RESULT,
    dl_command, type_handler, result_handler,
    cancel, cancel_callback, check_downloads,
    recent_command, start_command, help_command, myid_command,
)

logging.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)


def main():
    app = Application.builder().token(config.TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('recent', recent_command))
    app.add_handler(CommandHandler('myid', myid_command))

    conv = ConversationHandler(
        entry_points=[CommandHandler('dl', dl_command)],
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
    )
    app.add_handler(conv)
    app.job_queue.run_repeating(check_downloads, interval=60, first=10)
    logging.info("Bot started. Polling...")
    app.run_polling()


if __name__ == '__main__':
    main()
