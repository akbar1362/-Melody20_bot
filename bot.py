import logging
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from config import TELEGRAM_BOT_TOKEN
from handlers.start import start, help_command, settings_command, contact_command
from handlers.search import (
    search_command,
    download_callback,
    favorite_callback,
    noop_callback,
    popular_callback,
    text_search_handler,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set!")
        return

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CommandHandler("contact", contact_command))

    app.add_handler(CallbackQueryHandler(download_callback, pattern=r"^dl\d+$"))
    app.add_handler(CallbackQueryHandler(favorite_callback, pattern=r"^fav\d+$"))
    app.add_handler(CallbackQueryHandler(noop_callback, pattern=r"^noop$"))
    app.add_handler(CallbackQueryHandler(popular_callback, pattern=r"^popular$"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_search_handler))

    logger.info("Bot started! - Coded by Akbar Honarmand")
    app.run_polling()


if __name__ == "__main__":
    main()
