# handlers/admin_handler.py
import logging
from time import sleep
from telebot import TeleBot, types
from config import ADMIN_USER_IDS
import database
from locales import tr
from keyboards import get_main_keyboard, get_cancel_keyboard
from utils import is_message_valid

logger = logging.getLogger(__name__)

BROADCAST_TRIGGERS = {tr('btn_broadcast', l) for l in ['fa', 'en', 'ru']} | {'/broadcast'}
CANCEL_TRIGGERS = {tr('btn_cancel', l) for l in ['fa', 'en', 'ru']} | {'/cancel', 'cancel', 'لغو'}


def register_admin_handlers(bot: TeleBot, user_data: dict = None):

    def send_broadcast_message(message: types.Message):
        """Broadcast message received from admin to all registered users."""
        if not is_message_valid(message):
            return

        admin_id = message.chat.id
        admin_lang = database.get_user_language(admin_id) or 'fa'

        if not message.text:
            bot.send_message(admin_id, tr('admin_broadcast_prompt', admin_lang))
            return

        text = message.text.strip()
        if text in CANCEL_TRIGGERS:
            bot.send_message(admin_id, tr('cancelled', admin_lang), reply_markup=get_main_keyboard(admin_lang, is_admin=True))
            return

        user_ids = database.get_all_user_ids()
        if not user_ids:
            bot.send_message(admin_id, tr('no_users_found', admin_lang), reply_markup=get_main_keyboard(admin_lang, is_admin=True))
            return

        total_users = len(user_ids)
        success_count = 0

        progress_msg = bot.send_message(
            admin_id,
            tr('admin_broadcast_sending', admin_lang, total=total_users)
        )

        for i, uid in enumerate(user_ids):
            try:
                bot.send_message(uid, text)
                success_count += 1
                sleep(0.1)  # Brief pause to respect Telegram flood limits
            except Exception as e:
                logger.warning(f"Failed to send broadcast message to user {uid}: {e}")
                continue

            if (i + 1) % 10 == 0 or (i + 1) == total_users:
                try:
                    bot.edit_message_text(
                        chat_id=admin_id,
                        message_id=progress_msg.message_id,
                        text=tr('admin_broadcast_progress', admin_lang, current=i + 1, total=total_users)
                    )
                except Exception:
                    pass

        final_text = tr('admin_broadcast_done', admin_lang, success=success_count, total=total_users)
        try:
            bot.edit_message_text(
                chat_id=admin_id,
                message_id=progress_msg.message_id,
                text=final_text
            )
        except Exception:
            bot.send_message(admin_id, final_text)

        bot.send_message(admin_id, "✅", reply_markup=get_main_keyboard(admin_lang, is_admin=True))
        logger.info(f"Broadcast completed by admin {admin_id}: sent to {success_count}/{total_users} users.")

    @bot.message_handler(func=lambda message: message.text and message.text.strip() in BROADCAST_TRIGGERS)
    def handle_broadcast_command(message: types.Message):
        if not is_message_valid(message):
            return

        user_id = message.from_user.id
        admin_lang = database.get_user_language(user_id) or 'fa'

        if user_id not in ADMIN_USER_IDS:
            bot.send_message(message.chat.id, tr('admin_only', admin_lang))
            return

        bot.send_message(
            message.chat.id,
            tr('admin_broadcast_prompt', admin_lang),
            reply_markup=get_cancel_keyboard(admin_lang)
        )
        bot.register_next_step_handler(message, send_broadcast_message)