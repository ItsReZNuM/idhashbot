# keyboards.py
from telebot import types
from locales import tr, TEXTS


def get_language_inline_keyboard() -> types.InlineKeyboardMarkup:
    """Inline keyboard for selecting preferred language."""
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = [
        types.InlineKeyboardButton(TEXTS['fa']['lang_name'], callback_data="setlang_fa"),
        types.InlineKeyboardButton(TEXTS['en']['lang_name'], callback_data="setlang_en"),
        types.InlineKeyboardButton(TEXTS['ru']['lang_name'], callback_data="setlang_ru"),
    ]
    markup.add(*buttons)
    return markup


def get_main_keyboard(lang: str = 'fa', is_admin: bool = False) -> types.ReplyKeyboardMarkup:
    """Main reply keyboard customized by user language and admin privileges."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)

    # Share phone number button
    btn_phone = types.KeyboardButton(tr('btn_share_phone', lang), request_contact=True)
    markup.row(btn_phone)

    # Change language and cancel buttons
    btn_lang = types.KeyboardButton(tr('btn_change_lang', lang))
    btn_cancel = types.KeyboardButton(tr('btn_cancel', lang))
    markup.row(btn_lang, btn_cancel)

    # Admin broadcast button
    if is_admin:
        btn_broadcast = types.KeyboardButton(tr('btn_broadcast', lang))
        markup.row(btn_broadcast)

    return markup


def get_cancel_keyboard(lang: str = 'fa') -> types.ReplyKeyboardMarkup:
    """Minimal reply keyboard containing only the cancel button."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    btn_cancel = types.KeyboardButton(tr('btn_cancel', lang))
    markup.row(btn_cancel)
    return markup
