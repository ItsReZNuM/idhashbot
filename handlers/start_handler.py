# handlers/start_handler.py
import logging
from telebot import TeleBot, types
from config import ADMIN_USER_IDS
import database
from locales import tr
from keyboards import get_main_keyboard, get_language_inline_keyboard
from utils import is_message_valid, check_rate_limit

logger = logging.getLogger(__name__)

def register_start_handler(bot: TeleBot, user_data: dict):
    
    @bot.message_handler(commands=['start'])
    def send_welcome(message: types.Message):
        if not is_message_valid(message):
            return

        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name or "User"
        chat_id = message.chat.id

        # بررسی محدودیت نرخ ارسال پیام
        allowed, remaining = check_rate_limit(user_id)
        current_lang = database.get_user_language(user_id) or 'fa'
        if not allowed:
            bot.send_message(chat_id, tr('spam_warning', current_lang, remaining=remaining))
            return

        # پاک‌سازی وضعیت قبلی و بستن سشن در صورت وجود
        prev = user_data.get(chat_id)
        if prev and 'session' in prev and prev['session']:
            try:
                prev['session'].close()
            except Exception:
                pass
        user_data.pop(chat_id, None)

        # بررسی زبان ذخیره شده کاربر
        saved_lang = database.get_user_language(user_id)
        is_first_time = saved_lang is None

        if is_first_time:
            # تشخیص اولیه زبان از زبان تلگرام کاربر
            detected = 'fa'
            if message.from_user.language_code:
                code = message.from_user.language_code[:2].lower()
                if code in ['fa', 'en', 'ru']:
                    detected = code
                elif code in ['ru', 'uk', 'be', 'kk']:
                    detected = 'ru'
                else:
                    detected = 'en'

            database.add_user(user_id, username, first_name, detected)
            active_lang = detected
        else:
            active_lang = saved_lang
            database.add_user(user_id, username, first_name, active_lang)

        user_data[chat_id] = {
            'state': 'waiting_for_phone',
            'lang': active_lang
        }

        is_admin = user_id in ADMIN_USER_IDS

        # اگر کاربر بار اول است، کیبورد اینلاین انتخاب زبان را نیز ارسال می‌کنیم
        if is_first_time:
            bot.send_message(
                chat_id,
                tr('choose_language', active_lang),
                reply_markup=get_language_inline_keyboard()
            )

        welcome_text = tr('welcome', active_lang, name=first_name)
        bot.send_message(
            chat_id,
            welcome_text,
            reply_markup=get_main_keyboard(active_lang, is_admin),
            parse_mode='Markdown'
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith('setlang_'))
    def handle_language_callback(call: types.CallbackQuery):
        chat_id = call.message.chat.id
        user_id = call.from_user.id
        selected_lang = call.data.split('_')[1]

        database.set_user_language(user_id, selected_lang)

        if chat_id not in user_data:
            user_data[chat_id] = {}
        user_data[chat_id]['lang'] = selected_lang
        user_data[chat_id]['state'] = 'waiting_for_phone'

        bot.answer_callback_query(call.id, text=tr('language_selected', selected_lang))

        # ویرایش پیام اینلاین قبلی
        try:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=tr('language_selected', selected_lang)
            )
        except Exception:
            pass

        first_name = call.from_user.first_name or "User"
        is_admin = user_id in ADMIN_USER_IDS
        welcome_text = tr('welcome', selected_lang, name=first_name)

        bot.send_message(
            chat_id,
            welcome_text,
            reply_markup=get_main_keyboard(selected_lang, is_admin),
            parse_mode='Markdown'
        )