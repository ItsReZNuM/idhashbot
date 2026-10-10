# main.py
import logging
import telebot
import config
import database
from handlers.start_handler import register_start_handler
from handlers.api_handler import register_api_handlers
from handlers.admin_handler import register_admin_handlers
from handlers.other_handlers import register_other_handlers

# تنظیمات لاگ‌گیری
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ساخت نمونه ربات تلگرام
bot = telebot.TeleBot(config.TOKEN)

# دیکشنری نگهداری وضعیت و داده‌های موقت کاربران
user_data = {}


def setup_bot_commands():
    """ثبت لیست دستورات پیش‌فرض در منوی تلگرام."""
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
        logger.warning(f"عدم موفقیت در تنظیم دستورات تلگرام: {e}")


def main():
    """تابع اصلی راه‌اندازی و اجرای ربات."""
    if not config.TOKEN:
        logger.error("خطا: توکن ربات (TOKEN) در فایل .env تنظیم نشده است!")
        return

    # مقداردهی اولیه پایگاه داده و مایگریشن
    database.init_db()

    # ثبت منوی دستورات
    setup_bot_commands()

    # ثبت هندلرها
    register_start_handler(bot, user_data)
    register_api_handlers(bot, user_data)
    register_admin_handlers(bot, user_data)
    register_other_handlers(bot, user_data)

    logger.info("ربات دریافت API با موفقیت راه‌اندازی شد و در حال گوش دادن به پیام‌هاست...")

    # اجرای polling با مدیریت خطاهای اتصال
    bot.infinity_polling(skip_pending=True)


if __name__ == '__main__':
    main()