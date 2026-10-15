# handlers/api_handler.py
import re
import logging
import requests
from telebot import TeleBot, types
from config import ADMIN_USER_IDS
import database
from locales import tr
from keyboards import get_main_keyboard, get_cancel_keyboard, get_language_inline_keyboard
from utils import is_message_valid, check_rate_limit
from telegram_service import (
    BROWSER_HEADERS,
    normalize_phone_number,
    extract_login_code,
    send_telegram_code,
    login_and_get_credentials
)

logger = logging.getLogger(__name__)

# Control button labels across languages to prevent conflict with phone/code inputs
CANCEL_TEXTS = {tr('btn_cancel', l) for l in ['fa', 'en', 'ru']} | {'/cancel', 'cancel', 'لغو'}
LANG_TEXTS = {tr('btn_change_lang', l) for l in ['fa', 'en', 'ru']} | {'/lang', '/language'}
BROADCAST_TEXTS = {tr('btn_broadcast', l) for l in ['fa', 'en', 'ru']} | {'/broadcast'}


def safe_send_message(bot: TeleBot, chat_id: int, text: str, reply_markup=None, parse_mode: str = 'HTML'):
    """Send message with specified parse_mode, falling back to plain text if formatting fails."""
    try:
        return bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception as e:
        logger.warning(f"Error sending message with parse_mode={parse_mode}: {e}. Retrying without formatting.")
        plain_text = re.sub(r'<[^>]+>', '', text)
        return bot.send_message(chat_id, plain_text, reply_markup=reply_markup)


def register_api_handlers(bot: TeleBot, user_data: dict):

    @bot.message_handler(
        content_types=['contact', 'text'],
        func=lambda message: user_data.get(message.chat.id, {}).get('state') == 'waiting_for_phone'
    )
    def handle_phone_number(message: types.Message):
        if not is_message_valid(message):
            return

        user_id = message.from_user.id
        chat_id = message.chat.id
        lang = user_data.get(chat_id, {}).get('lang') or database.get_user_language(user_id) or 'fa'
        is_admin = user_id in ADMIN_USER_IDS

        # Rate limit check
        allowed, remaining = check_rate_limit(user_id)
        if not allowed:
            safe_send_message(bot, chat_id, tr('spam_warning', lang, remaining=remaining))
            return

        # Check for system buttons clicked during phone prompt
        if message.text:
            text_val = message.text.strip()
            if text_val in CANCEL_TEXTS:
                user_data.pop(chat_id, None)
                safe_send_message(bot, chat_id, tr('cancelled', lang), reply_markup=get_main_keyboard(lang, is_admin))
                return
            if text_val in LANG_TEXTS:
                safe_send_message(bot, chat_id, tr('choose_language', lang), reply_markup=get_language_inline_keyboard())
                return
            if text_val in BROADCAST_TEXTS and is_admin:
                return  # Handled by admin_handler

        raw_phone = ""
        if message.contact:
            raw_phone = message.contact.phone_number
        elif message.text:
            raw_phone = message.text.strip()
        else:
            safe_send_message(bot, chat_id, tr('invalid_phone', lang))
            return

        phone_number = normalize_phone_number(raw_phone)
        if not phone_number:
            safe_send_message(bot, chat_id, tr('invalid_phone', lang))
            return

        # Acknowledge phone received and request login code
        safe_send_message(bot, chat_id, tr('phone_received', lang, phone=phone_number))

        session = requests.Session()
        session.headers.update(BROWSER_HEADERS)

        success, status_or_err, random_hash = send_telegram_code(session, phone_number)

        if not success:
            session.close()
            user_data.pop(chat_id, None)

            if status_or_err == 'rate_limited':
                safe_send_message(bot, chat_id, tr('telegram_rate_limited', lang), reply_markup=get_main_keyboard(lang, is_admin))
            elif status_or_err.startswith('network_error:'):
                err_detail = status_or_err.split(':', 1)[1]
                safe_send_message(bot, chat_id, tr('network_error', lang, error=err_detail), reply_markup=get_main_keyboard(lang, is_admin))
            else:
                safe_send_message(bot, chat_id, tr('login_failed', lang, error=status_or_err), reply_markup=get_main_keyboard(lang, is_admin))
            return

        # Preserve active HTTP session for subsequent verification step
        user_data[chat_id] = {
            'state': 'waiting_for_code',
            'phone': phone_number,
            'random_hash': random_hash,
            'session': session,
            'lang': lang
        }

        safe_send_message(bot, chat_id, tr('enter_code', lang), reply_markup=get_cancel_keyboard(lang))

    @bot.message_handler(
        content_types=['text'],
        func=lambda message: user_data.get(message.chat.id, {}).get('state') == 'waiting_for_code'
    )
    def handle_login_code(message: types.Message):
        if not is_message_valid(message):
            return

        user_id = message.from_user.id
        chat_id = message.chat.id
        info = user_data.get(chat_id, {})
        lang = info.get('lang') or database.get_user_language(user_id) or 'fa'
        is_admin = user_id in ADMIN_USER_IDS

        # Rate limit check
        allowed, remaining = check_rate_limit(user_id)
        if not allowed:
            safe_send_message(bot, chat_id, tr('spam_warning', lang, remaining=remaining))
            return

        raw_text = message.text.strip() if message.text else ""

        # Handle cancellation
        if raw_text in CANCEL_TEXTS:
            session = info.get('session')
            if session:
                try:
                    session.close()
                except Exception:
                    pass
            user_data.pop(chat_id, None)
            safe_send_message(bot, chat_id, tr('cancelled', lang), reply_markup=get_main_keyboard(lang, is_admin))
            return

        if not info or 'session' not in info or 'random_hash' not in info or 'phone' not in info:
            safe_send_message(bot, chat_id, tr('session_expired', lang), reply_markup=get_main_keyboard(lang, is_admin))
            user_data.pop(chat_id, None)
            return

        code = extract_login_code(raw_text)

        # Validate code structure (letters, digits, underscores, hyphens, 4 to 25 chars)
        if not re.match(r'^[a-zA-Z0-9_\-]{4,25}$', code):
            safe_send_message(bot, chat_id, tr('code_invalid_format', lang), reply_markup=get_cancel_keyboard(lang))
            return

        session = info['session']
        phone_number = info['phone']
        random_hash = info['random_hash']

        safe_send_message(bot, chat_id, tr('logging_in', lang))

        try:
            success, creds, err_code = login_and_get_credentials(session, phone_number, random_hash, code)

            if success and creds:
                resp = tr('credentials_success', lang, api_id=creds['api_id'], api_hash=creds['api_hash'])
                if creds.get('public_key'):
                    resp += tr('public_key_text', lang, key=creds['public_key'])
                if creds.get('prod_config'):
                    resp += tr('prod_config_text', lang, pc=creds['prod_config'])
                resp += tr('credentials_footer', lang)

                safe_send_message(bot, chat_id, resp, reply_markup=get_main_keyboard(lang, is_admin), parse_mode='HTML')
            else:
                # Handle error categories
                if err_code == 'session_expired':
                    error_msg = tr('session_expired', lang)
                elif err_code in ['app_creation_rejected', 'app_creation_failed']:
                    error_msg = tr('app_creation_failed', lang)
                elif err_code == 'app_creation_flood':
                    error_msg = tr('app_creation_flood', lang)
                elif err_code.startswith('account_restricted'):
                    detail = err_code.split(':', 1)[1] if ':' in err_code else ""
                    if not detail:
                        detail = tr('account_restricted_generic', lang)
                    error_msg = tr('account_restricted', lang, detail=detail)
                elif err_code.startswith('login_failed:'):
                    detail = err_code.split(':', 1)[1]
                    error_msg = tr('login_failed', lang, error=detail)
                elif err_code.startswith('network_error:'):
                    detail = err_code.split(':', 1)[1]
                    error_msg = tr('network_error', lang, error=detail)
                elif err_code == 'credentials_not_found':
                    error_msg = tr('credentials_not_found', lang)
                else:
                    error_msg = tr('login_failed', lang, error=err_code)

                safe_send_message(bot, chat_id, error_msg, reply_markup=get_main_keyboard(lang, is_admin))

        except Exception as e:
            logger.error(f"Unexpected error in handle_login_code: {e}", exc_info=True)
            safe_send_message(bot, chat_id, tr('login_failed', lang, error=str(e)), reply_markup=get_main_keyboard(lang, is_admin))
        finally:
            try:
                session.close()
            except Exception:
                pass
            user_data.pop(chat_id, None)