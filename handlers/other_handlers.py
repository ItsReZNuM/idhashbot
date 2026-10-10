# handlers/other_handlers.py
import logging
from telebot import TeleBot, types
from config import ADMIN_USER_IDS
import database
from locales import tr
from keyboards import get_main_keyboard, get_language_inline_keyboard
from utils import is_message_valid, check_rate_limit

logger = logging.getLogger(__name__)

LANG_TRIGGERS = {tr('btn_change_lang', l) for l in ['fa', 'en', 'ru']} | {'/lang', '/language'}
CANCEL_TRIGGERS = {tr('btn_cancel', l) for l in ['fa', 'en', 'ru']} | {'/cancel', 'cancel', 'لغو'}


def register_other_handlers(bot: TeleBot, user_data: dict):

    @bot.message_handler(commands=['alive'])
    def handle_alive(message: types.Message):
        if not is_message_valid(message):
            return

        user_id = message.from_user.id
        allowed, remaining = check_rate_limit(user_id)
        lang = database.get_user_language(user_id) or 'fa'

        if not allowed:
            bot.send_message(message.chat.id, tr('spam_warning', lang, remaining=remaining))
            return

        bot.send_message(message.chat.id, tr('alive', lang))

    @bot.message_handler(commands=['help'])
    def handle_help(message: types.Message):
        if not is_message_valid(message):
            return

        user_id = message.from_user.id
        allowed, remaining = check_rate_limit(user_id)
        lang = database.get_user_language(user_id) or 'fa'

        if not allowed:
            bot.send_message(message.chat.id, tr('spam_warning', lang, remaining=remaining))
            return

        bot.send_message(message.chat.id, tr('help', lang), parse_mode='Markdown')

    @bot.message_handler(commands=['lang', 'language'])
    @bot.message_handler(func=lambda message: message.text and message.text.strip() in LANG_TRIGGERS)
    def handle_language_prompt(message: types.Message):
        if not is_message_valid(message):
            return

        user_id = message.from_user.id
        lang = database.get_user_language(user_id) or 'fa'

        bot.send_message(
            message.chat.id,
            tr('choose_language', lang),
            reply_markup=get_language_inline_keyboard()
        )

    @bot.message_handler(commands=['cancel'])
    @bot.message_handler(func=lambda message: message.text and message.text.strip() in CANCEL_TRIGGERS)
    def handle_cancel(message: types.Message):
        if not is_message_valid(message):
            return

        chat_id = message.chat.id
        user_id = message.from_user.id
        lang = user_data.get(chat_id, {}).get('lang') or database.get_user_language(user_id) or 'fa'
        is_admin = user_id in ADMIN_USER_IDS

        info = user_data.get(chat_id)
        if info and 'session' in info and info['session']:
            try:
                info['session'].close()
            except Exception:
                pass

        user_data.pop(chat_id, None)
        bot.send_message(
            chat_id,
            tr('cancelled', lang),
            reply_markup=get_main_keyboard(lang, is_admin)
        )