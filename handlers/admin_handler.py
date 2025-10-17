# handlers/admin_handler.py
import logging
from time import sleep
from config import ADMIN_USER_IDS
import database
from utils import is_message_valid

logger = logging.getLogger(__name__)

def register_admin_handlers(bot):
    def send_broadcast_message(message):
        """پیام دریافت شده از ادمین را به همه کاربران ارسال می‌کند."""
        if not is_message_valid(message):
            return
        
        admin_id = message.chat.id
        
        # دریافت لیست آیدی کاربران از پایگاه داده
        user_ids = database.get_all_user_ids()
        if not user_ids:
            bot.send_message(admin_id, "❌ کاربری در پایگاه داده یافت نشد!")
            return
            
        success_count = 0
        total_users = len(user_ids)
        
        # ارسال پیام اولیه به ادمین
        progress_message = bot.send_message(admin_id, f"⏳ در حال ارسال پیام به {total_users} کاربر...")
        
        for i, user_id in enumerate(user_ids):
            try:
                bot.send_message(user_id, message.text)
                success_count += 1
                sleep(0.5) # وقفه کوتاه برای جلوگیری از بلاک شدن
                
                # ویرایش پیام پیشرفت در بازه‌های مشخص
                if (i + 1) % 10 == 0 or (i + 1) == total_users:
                    bot.edit_message_text(
                        chat_id=admin_id,
                        message_id=progress_message.message_id,
                        text=f"⏳ در حال ارسال... ({i + 1}/{total_users})"
                    )
            except Exception as e:
                logger.warning(f"ارسال پیام به کاربر {user_id} ناموفق بود: {e}")
                continue
                
        final_message = f"پیام به {success_count} کاربر از مجموع {total_users} کاربر با موفقیت ارسال شد 📢"
        bot.edit_message_text(
            chat_id=admin_id,
            message_id=progress_message.message_id,
            text=final_message
        )
        logger.info(f"پیام همگانی توسط ادمین {admin_id} به {success_count} کاربر ارسال شد.")


    @bot.message_handler(func=lambda message: message.text == "پیام همگانی 📢")
    def handle_broadcast(message):
        if not is_message_valid(message):
            return
            
        user_id = message.chat.id
        if user_id not in ADMIN_USER_IDS:
            bot.send_message(user_id, "این قابلیت فقط برای ادمین‌ها در دسترس است!")
            return
            
        logger.info(f"ادمین {user_id} فرآیند پیام همگانی را آغاز کرد.")
        bot.send_message(user_id, "هر پیامی که می‌خواهی بنویس تا برای همه کاربران ارسال شود 📢")
        bot.register_next_step_handler(message, send_broadcast_message)