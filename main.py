# main.py
import telebot
import logging
import config
import database

# وارد کردن توابع ثبت هندلرها
from handlers.start_handler import register_start_handler
from handlers.api_handler import register_api_handlers
from handlers.admin_handler import register_admin_handlers
from handlers.other_handlers import register_other_handlers

# تنظیمات لاگ‌گیری
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ساخت نمونه ربات
bot = telebot.TeleBot(config.TOKEN)

# دیکشنری برای نگهداری وضعیت کاربران (در حافظه)
user_data = {}

def main():
    """تابع اصلی برای راه‌اندازی ربات."""
    
    # مقداردهی اولیه پایگاه داده
    database.init_db()

    # ثبت دستورات ربات
    commands = [
        telebot.types.BotCommand("start", "شروع ربات"),
        telebot.types.BotCommand("alive", "چک کردن وضعیت ربات"),
    ]
    bot.set_my_commands(commands)
    
    # ثبت تمام هندلرها از فایل‌های مختلف
    register_start_handler(bot, user_data)
    register_api_handlers(bot, user_data)
    register_admin_handlers(bot)
    register_other_handlers(bot)

    logger.info("ربات با موفقیت راه‌اندازی شد و در حال اجرا است...")
    
    # اجرای ربات
    bot.polling(none_stop=True)

if __name__ == '__main__':
    main()