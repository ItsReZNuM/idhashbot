# main.py
import logging
import telebot
import config
import database
from handlers.start_handler import register_start_handler
from handlers.api_handler import register_api_handlers
from handlers.admin_handler import register_admin_handlers
from handlers.other_handlers import register_other_handlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize TeleBot instance
bot = telebot.TeleBot(config.TOKEN)

# In-memory dictionary for user sessions and state management
user_data = {}


def setup_bot_commands():
    """Register default commands menu with Telegram."""
    commands = [
        telebot.types.BotCommand("start", "🚀 Start / شروع / Запуск"),
        telebot.types.BotCommand("lang", "🌐 Language / تغییر زبان / Язык"),
        telebot.types.BotCommand("help", "ℹ️ Help / راهنما / Помощь"),
        telebot.types.BotCommand("cancel", "❌ Cancel / لغو عملیات / Отмена"),
        telebot.types.BotCommand("alive", "🤖 Check status / بررسی وضعیت"),
    ]
    try:
        bot.set_my_commands(commands)
    except Exception as e:
        logger.warning(f"Could not register bot commands with Telegram: {e}")


def main():
    """Main application entry point."""
    if not config.TOKEN:
        logger.error("Error: Bot TOKEN is missing or empty in .env configuration!")
        return

    # Initialize SQLite database and run migrations
    database.init_db()

    # Set up Telegram menu commands
    setup_bot_commands()

    # Register all handlers
    register_start_handler(bot, user_data)
    register_api_handlers(bot, user_data)
    register_admin_handlers(bot, user_data)
    register_other_handlers(bot, user_data)

    logger.info("Telegram API ID & Hash Bot started successfully. Listening for updates...")

    # Start long polling with resilient connection handling
    bot.infinity_polling(skip_pending=True)


if __name__ == '__main__':
    main()