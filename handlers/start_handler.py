# handlers/start_handler.py
from telebot import types
from config import ADMIN_USER_IDS
import database
from utils import is_message_valid, check_rate_limit

def register_start_handler(bot, user_data):
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        if not is_message_valid(message):
            return
        
        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        
        # ذخیره کاربر در پایگاه داده SQLite
        database.add_user(user_id, username, first_name)

        allowed, error_message = check_rate_limit(user_id)
        if not allowed:
            bot.send_message(user_id, error_message)
            return
        
        chat_id = message.chat.id
        
        if user_id in ADMIN_USER_IDS:
            user_data[chat_id] = {'state': 'admin_menu'}
        else:
            user_data[chat_id] = {'state': 'waiting_for_phone'} 

        welcome_message = (
            f"👋 سلام {first_name} عزیز! به ربات دریافت API تلگرام خوش آمدید!\n\n"
            "این ربات به شما کمک می‌کند تا API ID و API Hash حساب تلگرام خود را به راحتی دریافت کنید. "
            "این اطلاعات برای توسعه‌دهندگان و افرادی که می‌خواهند با API تلگرام کار کنند، مفید است.\n\n"
            "⚠️ توجه: شماره موبایل شما نزد ما محفوظ است و در هیچ کجا ذخیره نمی‌شود. "
            "فرآیند دریافت API کاملاً امن است و مستقیماً از طریق تلگرام انجام می‌شود.\n\n"
            "برای شروع، لطفاً شماره موبایل خود را به همراه کد کشور (مثال: +989123456789) ارسال کنید."
        )
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        button_phone = types.KeyboardButton("اشتراک گذاری شماره موبایل 📱", request_contact=True)
        markup.add(button_phone)
        
        if user_id in ADMIN_USER_IDS:
            btn_special = types.KeyboardButton("پیام همگانی 📢")
            markup.add(btn_special)
        
        bot.send_message(chat_id, welcome_message, reply_markup=markup)
        if user_id in ADMIN_USER_IDS:
            bot.send_message(chat_id, "شما ادمین هستید! می‌توانید از دکمه 'پیام همگانی 📢' برای ارسال پیام به همه کاربران استفاده کنید.")
        else:
            bot.send_message(chat_id, "لطفاً شماره موبایل خود را برای دریافت API ID و API Hash ارسال کنید "
                                       "(می‌توانید آن را تایپ کنید یا با دکمه زیر به اشتراک بگذارید):")