# locales.py
"""
ماژول محلی‌سازی و پشتیبانی از چند زبانگی (فارسی، انگلیسی، روسی)
Localization module supporting Persian (fa), English (en), and Russian (ru).
"""

TEXTS = {
    'fa': {
        'choose_language': "🌐 لطفاً زبان مورد نظر خود را انتخاب کنید:\n\n🌐 Please select your language:\n\n🌐 Пожалуйста, выберите язык:",
        'language_selected': "✅ زبان فارسی انتخاب شد.",
        'lang_name': "🇮🇷 فارسی",
        
        'welcome': (
            "👋 سلام *{name}* عزیز! به ربات دریافت API تلگرام خوش آمدید!\n\n"
            "این ربات به شما کمک می‌کند تا **API ID** و **API Hash** حساب تلگرام خود را به صورت خودکار و امن دریافت کنید.\n\n"
            "⚠️ **نکته امنیتی:**\n"
            "ارتباط مستقیماً با سرور رسمی تلگرام (`my.telegram.org`) انجام می‌شود و هیچ اطلاعاتی در سرور ذخیره نمی‌شود.\n\n"
            "📱 برای شروع، شماره موبایل خود را به همراه کد کشور ارسال کنید (مثال: `+989123456789`) یا از دکمه زیر برای اشتراک‌گذاری استفاده نمایید:"
        ),
        
        'btn_share_phone': "اشتراک گذاری شماره موبایل 📱",
        'btn_change_lang': "🌐 تغییر زبان / Language",
        'btn_cancel': "❌ لغو عملیات",
        'btn_broadcast': "پیام همگانی 📢",
        
        'cancelled': "❌ عملیات لغو شد. برای شروع مجدد /start را ارسال کنید.",
        'invalid_phone': "❌ فرمت شماره موبایل نامعتبر است.\nلطفاً شماره را به همراه کد کشور وارد کنید (مثال: `+989123456789`).",
        'phone_received': "📱 شماره `{phone}` ثبت شد.\n⏳ در حال درخواست کد تأیید از تلگرام...",
        
        'telegram_rate_limited': "🚫 حساب شما به دلیل تلاش‌های مکرر موقتاً توسط تلگرام محدود شده است!\nلطفاً ۸ الی ۲۴ ساعت دیگر دوباره امتحان کنید.",
        'enter_code': "✉️ کد ورود ارسال شده توسط تلگرام را وارد کنید:\n(می‌توانید پیام حاوی کد تلگرام را مستقیماً فوروارد کنید)",
        
        'code_invalid_format': "⚠️ کد وارد شده نامعتبر است. لطفاً کد را با دقت بررسی و مجدداً ارسال کنید.",
        'logging_in': "🔐 در حال بررسی کد و ورود به my.telegram.org...",
        'login_failed': "❌ ورود به حساب ناموفق بود.\nعلت: {error}\nلطفاً از صحت کد و منقضی نشدن آن اطمینان حاصل کرده و با /start دوباره تلاش کنید.",
        
        'session_expired': "❌ سشن منقضی شد یا به صفحه ورود هدایت شدید. لطفاً با /start مجدداً تلاش کنید.",
        'creating_app': "⚙️ اپلیکیشنی در حساب شما یافت نشد. در حال ساخت خودکار برنامه در تلگرام...",
        'app_creation_failed': (
            "❌ تلگرام اجازه ساخت خودکار برنامه را به این حساب نداد.\n\n"
            "💡 ممکن است اکانت شما به تازگی ساخته شده باشد یا آی‌پی محدود باشد. لطفاً یک بار وارد سایت https://my.telegram.org در مرورگر خود شوید و برنامه را بسازید، سپس دوباره تست کنید."
        ),
        'credentials_success': (
            "🎉 **اطلاعات API تلگرام شما با موفقیت دریافت شد!**\n\n"
            "🔑 **API ID:** `{api_id}`\n"
            "🔒 **API HASH:** `{api_hash}`\n"
        ),
        'public_key_text': "🧩 **Public Key:**\n`{key}`\n",
        'prod_config_text': "⚙️ **Production Config:** `{pc}`\n",
        'credentials_footer': "\n💡 از این اطلاعات می‌توانید در پروژه‌های تله‌تون (Telethon)، پایروگرام (Pyrogram) و کلاینت‌های اختصاصی تلگرام استفاده کنید.",
        'credentials_not_found': "❌ اطلاعات API در صفحه یافت نشد. ممکن است حساب دارای محدودیت باشد یا قالب صفحه تغییر کرده باشد.",
        
        'network_error': "❌ خطای شبکه در ارتباط با سرورهای تلگرام: {error}\nلطفاً بعداً دوباره امتحان کنید.",
        'spam_warning': "⚠️ ارسال پیام بسیار سریع است! لطفاً {remaining} ثانیه صبر کنید.",
        
        'alive': "🤖 ربات فعال و آماده به کار است!",
        'help': (
            "ℹ️ **راهنمای ربات دریافت API تلگرام:**\n\n"
            "1️⃣ شماره موبایل خود را به همراه کد کشور ارسال کنید (مثال: `+989123456789`).\n"
            "2️⃣ تلگرام یک کد تأیید برای حساب شما ارسال می‌کند.\n"
            "3️⃣ کد را وارد کرده یا پیام تلگرام را فوروارد نمایید.\n"
            "4️⃣ ربات به صورت خودکار اطلاعات API شما را دریافت و نمایش می‌دهد.\n\n"
            "دستورات مفید:\n"
            "/start - شروع یا شروع مجدد\n"
            "/lang - تغییر زبان ربات\n"
            "/cancel - لغو عملیات جاری\n"
            "/alive - بررسی وضعیت ربات"
        ),
        
        'admin_only': "⛔ این دستور فقط برای ادمین‌های ربات مجاز است.",
        'admin_broadcast_prompt': "📢 لطفاً پیامی که می‌خواهید برای تمام کاربران ارسال شود را بفرستید:",
        'admin_broadcast_sending': "⏳ در حال ارسال پیام همگانی به {total} کاربر...",
        'admin_broadcast_progress': "⏳ در حال ارسال... ({current}/{total})",
        'admin_broadcast_done': "✅ پیام همگانی با موفقیت به {success} نفر از مجموع {total} کاربر ارسال شد.",
        'no_users_found': "❌ هیچ کاربری در دیتابیس ثبت نشده است.",
    },
    
    'en': {
        'choose_language': "🌐 Please select your language:\n\n🌐 لطفاً زبان مورد نظر خود را انتخاب کنید:\n\n🌐 Пожалуйста, выберите язык:",
        'language_selected': "✅ English language selected.",
        'lang_name': "🇬🇧 English",
        
        'welcome': (
            "👋 Hello *{name}*! Welcome to the Telegram API ID & Hash Bot!\n\n"
            "This bot helps you easily and automatically retrieve the **API ID** and **API Hash** for your Telegram account.\n\n"
            "⚠️ **Security Notice:**\n"
            "Requests are made directly to the official Telegram site (`my.telegram.org`). Your phone number and credentials are never stored.\n\n"
            "📱 To start, please send your phone number with country code (e.g. `+1234567890`) or use the button below to share it:"
        ),
        
        'btn_share_phone': "Share Phone Number 📱",
        'btn_change_lang': "🌐 Change Language",
        'btn_cancel': "❌ Cancel",
        'btn_broadcast': "Broadcast Message 📢",
        
        'cancelled': "❌ Operation cancelled. Send /start to begin again.",
        'invalid_phone': "❌ Invalid phone number format.\nPlease enter your phone number with country code (e.g. `+1234567890`).",
        'phone_received': "📱 Phone `{phone}` received.\n⏳ Requesting confirmation code from Telegram...",
        
        'telegram_rate_limited': "🚫 Your account is temporarily rate-limited by Telegram due to multiple attempts!\nPlease wait 8 to 24 hours before trying again.",
        'enter_code': "✉️ Please enter the confirmation code sent to your Telegram account:\n(You can also directly forward the official Telegram message)",
        
        'code_invalid_format': "⚠️ Invalid confirmation code format. Please check and send it again.",
        'logging_in': "🔐 Verifying confirmation code and accessing my.telegram.org...",
        'login_failed': "❌ Telegram login failed.\nReason: {error}\nPlease make sure the code is correct and hasn't expired, then send /start to retry.",
        
        'session_expired': "❌ Session expired or redirected to login. Please start over with /start.",
        'creating_app': "⚙️ No existing Telegram app found. Automatically creating an application...",
        'app_creation_failed': (
            "❌ Telegram rejected creating an application automatically for this account.\n\n"
            "💡 Brand-new accounts or certain IP addresses may be restricted. Please visit https://my.telegram.org manually in your browser to create the app once, then try again."
        ),
        'credentials_success': (
            "🎉 **Telegram API credentials retrieved successfully!**\n\n"
            "🔑 **API ID:** `{api_id}`\n"
            "🔒 **API HASH:** `{api_hash}`\n"
        ),
        'public_key_text': "🧩 **Public Key:**\n`{key}`\n",
        'prod_config_text': "⚙️ **Production Config:** `{pc}`\n",
        'credentials_footer': "\n💡 You can now use these credentials in Telethon, Pyrogram, and custom Telegram MTProto applications.",
        'credentials_not_found': "❌ Could not parse API credentials from Telegram. Your account may have restrictions or the layout changed.",
        
        'network_error': "❌ Network error communicating with Telegram servers: {error}\nPlease try again later.",
        'spam_warning': "⚠️ You are sending messages too quickly! Please wait {remaining} seconds.",
        
        'alive': "🤖 Bot is alive and running!",
        'help': (
            "ℹ️ **Telegram API Bot Guide:**\n\n"
            "1️⃣ Send your phone number with country code (e.g. `+1234567890`).\n"
            "2️⃣ Telegram will send an official login code to your account.\n"
            "3️⃣ Enter the code or forward the Telegram message.\n"
            "4️⃣ The bot will automatically retrieve and display your API credentials.\n\n"
            "Available commands:\n"
            "/start - Start or restart the bot\n"
            "/lang - Change bot language\n"
            "/cancel - Cancel current operation\n"
            "/alive - Check bot status"
        ),
        
        'admin_only': "⛔ This command is only available to bot administrators.",
        'admin_broadcast_prompt': "📢 Please send the message you want to broadcast to all users:",
        'admin_broadcast_sending': "⏳ Broadcasting message to {total} users...",
        'admin_broadcast_progress': "⏳ Sending... ({current}/{total})",
        'admin_broadcast_done': "✅ Broadcast completed! Sent to {success} out of {total} users.",
        'no_users_found': "❌ No users found in the database.",
    },
    
    'ru': {
        'choose_language': "🌐 Пожалуйста, выберите язык:\n\n🌐 لطفاً زبان مورد نظر خود را انتخاب کنید:\n\n🌐 Please select your language:",
        'language_selected': "✅ Выбран русский язык.",
        'lang_name': "🇷🇺 Русский",
        
        'welcome': (
            "👋 Здравствуйте, *{name}*! Добро пожаловать в бот для получения Telegram API ID и Hash!\n\n"
            "Этот бот поможет вам быстро и безопасно получить **API ID** и **API Hash** для вашей учетной записи Telegram.\n\n"
            "⚠️ **Примечание о безопасности:**\n"
            "Запросы отправляются напрямую на официальный сайт Telegram (`my.telegram.org`). Номер и коды нигде не сохраняются.\n\n"
            "📱 Для начала отправьте свой номер телефона с кодом страны (например, `+79123456789`) или воспользуйтесь кнопкой ниже:"
        ),
        
        'btn_share_phone': "Поделиться номером 📱",
        'btn_change_lang': "🌐 Сменить язык / Language",
        'btn_cancel': "❌ Отмена",
        'btn_broadcast': "Массовая рассылка 📢",
        
        'cancelled': "❌ Операция отменена. Отправьте /start, чтобы начать заново.",
        'invalid_phone': "❌ Неверный формат номера телефона.\nПожалуйста, введите номер с кодом страны (например: `+79123456789`).",
        'phone_received': "📱 Номер `{phone}` получен.\n⏳ Запрос кода подтверждения у Telegram...",
        
        'telegram_rate_limited': "🚫 Ваш аккауنت временно ограничен Telegram из-за частых попыток!\nПожалуйста, повторите попытку через 8–24 часа.",
        'enter_code': "✉️ Пожалуйста, введите код подтверждения от Telegram:\n(Вы также можете просто переслать служебное сообщение из Telegram)",
        
        'code_invalid_format': "⚠️ Неверный формат кода. Пожалуйста, проверьте и отправьте еще раз.",
        'logging_in': "🔐 Проверка кода и вход на my.telegram.org...",
        'login_failed': "❌ Ошибка входа в аккаунт Telegram.\nПричина: {error}\nУбедитесь, что код верный и не истек, затем отправьте /start снова.",
        
        'session_expired': "❌ Сессия истекла или произошла переадресация на страницу входа. Начните заново с /start.",
        'creating_app': "⚙️ Приложение не найдено. Автоматическое создание приложения в Telegram...",
        'app_creation_failed': (
            "❌ Telegram отклонил автоматическое создание приложения для этого аккаунта.\n\n"
            "💡 Новые аккаунты или подозрительные IP могут иметь ограничения. Войдите на https://my.telegram.org в браузере вручную и создайте приложение, затем повторите попытку."
        ),
        'credentials_success': (
            "🎉 **Данные Telegram API успешно получены!**\n\n"
            "🔑 **API ID:** `{api_id}`\n"
            "🔒 **API HASH:** `{api_hash}`\n"
        ),
        'public_key_text': "🧩 **Public Key:**\n`{key}`\n",
        'prod_config_text': "⚙️ **Production Config:** `{pc}`\n",
        'credentials_footer': "\n💡 Вы можете использовать эти данные в проектах на Telethon, Pyrogram и других MTProto клиентах.",
        'credentials_not_found': "❌ Не удалось извлечь данные API. Возможно, на аккаунте есть ограничения или изменилась структура сайта.",
        
        'network_error': "❌ Сетевая ошибка при подключении к серверам Telegram: {error}\nПожалуйста, попробуйте позже.",
        'spam_warning': "⚠️ Вы отправляете сообщения слишком часто! Подождите {remaining} сек.",
        
        'alive': "🤖 Бот активен и работает!",
        'help': (
            "ℹ️ **Инструкция по использованию бота:**\n\n"
            "1️⃣ Отправьте номер телефона с кодом страны (например, `+79123456789`).\n"
            "2️⃣ Telegram отправит служебное сообщение с кодом подтверждения.\n"
            "3️⃣ Введите полученный код или перешлите сообщение от Telegram.\n"
            "4️⃣ Бот автоматически получит и покажет ваши данные API.\n\n"
            "Доступные команды:\n"
            "/start - Запуск или перезапуск бота\n"
            "/lang - Сменить язык бота\n"
            "/cancel - Отменить текущее действие\n"
            "/alive - Проверить работоспособность бота"
        ),
        
        'admin_only': "⛔ Эта команда доступна только администраторам бота.",
        'admin_broadcast_prompt': "📢 Отправьте сообщение, которое хотите разослать всем пользователям:",
        'admin_broadcast_sending': "⏳ Рассылка сообщения {total} пользователям...",
        'admin_broadcast_progress': "⏳ Отправка... ({current}/{total})",
        'admin_broadcast_done': "✅ Рассылка завершена! Отправлено {success} из {total} пользователей.",
        'no_users_found': "❌ В базе данных нет пользователей.",
    }
}

SUPPORTED_LANGUAGES = ['fa', 'en', 'ru']

def tr(key: str, lang: str = 'fa', **kwargs) -> str:
    """ترجمه کلید با زبان مشخص، در صورت نبود به فارسی برمی‌گردد."""
    if lang not in TEXTS:
        lang = 'fa'
    text = TEXTS[lang].get(key, TEXTS['fa'].get(key, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
