# handlers/start_handler.py
import re
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

        # Check rate limit
        allowed, remaining = check_rate_limit(user_id)
        current_lang = database.get_user_language(user_id) or 'fa'
        if not allowed:
            bot.send_message(chat_id, tr('spam_warning', current_lang, remaining=remaining))
            return

        # Clean up existing state and close active session if present
        prev = user_data.get(chat_id)
        if prev and 'session' in prev and prev['session']:
            try:
                prev['session'].close()
            except Exception:
                pass
        user_data.pop(chat_id, None)

        # Check if user has an existing saved language in the database
        saved_lang = database.get_user_language(user_id)

        if not saved_lang:
            # First time user: Ask for language FIRST before showing any welcome text
            user_data[chat_id] = {
                'state': 'waiting_for_lang'
            }
            bot.send_message(
                chat_id,
                tr('choose_language', 'fa'),
                reply_markup=get_language_inline_keyboard()
            )
            return

        # Returning user: proceed directly with their chosen language
        user_data[chat_id] = {
            'state': 'waiting_for_phone',
            'lang': saved_lang
        }

        database.add_user(user_id, username, first_name, saved_lang)
        is_admin = user_id in ADMIN_USER_IDS
        welcome_text = tr('welcome', saved_lang, name=first_name)

        try:
            bot.send_message(
                chat_id,
                welcome_text,
                reply_markup=get_main_keyboard(saved_lang, is_admin),
                parse_mode='HTML'
            )
        except Exception:
            bot.send_message(
                chat_id,
                re.sub(r'<[^>]+>', '', welcome_text),
                reply_markup=get_main_keyboard(saved_lang, is_admin)
            )

    @bot.callback_query_handler(func=lambda call: call.data.startswith('setlang_'))
    def handle_language_callback(call: types.CallbackQuery):
        chat_id = call.message.chat.id
        user_id = call.from_user.id
        selected_lang = call.data.split('_')[1]

        # Save selected language in DB
        database.set_user_language(user_id, selected_lang)
        first_name = call.from_user.first_name or "User"
        username = call.from_user.username
        database.add_user(user_id, username, first_name, selected_lang)

        if chat_id not in user_data:
            user_data[chat_id] = {}
        user_data[chat_id]['lang'] = selected_lang
        user_data[chat_id]['state'] = 'waiting_for_phone'

        bot.answer_callback_query(call.id, text=tr('language_selected', selected_lang))

        # Acknowledge language selection by updating the inline message
        try:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=tr('language_selected', selected_lang)
            )
        except Exception:
            pass

        is_admin = user_id in ADMIN_USER_IDS
        welcome_text = tr('welcome', selected_lang, name=first_name)

        try:
            bot.send_message(
                chat_id,
                welcome_text,
                reply_markup=get_main_keyboard(selected_lang, is_admin),
                parse_mode='HTML'
            )
        except Exception:
            bot.send_message(
                chat_id,
                re.sub(r'<[^>]+>', '', welcome_text),
                reply_markup=get_main_keyboard(selected_lang, is_admin)
            )