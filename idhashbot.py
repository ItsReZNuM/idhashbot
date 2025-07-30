import telebot
from telebot import types
import requests
from bs4 import BeautifulSoup
import re
import os
from datetime import datetime
from pytz import timezone
from logging import getLogger
from time import time , sleep
import json
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)
logger = getLogger(__name__)
message_tracker = {}
user_data = {}
ADMIN_USER_IDS = os.getenv('ADMIN_USER_IDS')
USERS_FILE = "users.json"

def save_user(user_id, username):
    if user_id in ADMIN_USER_IDS:
        return
    users = []
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                users = json.load(f)
        except json.JSONDecodeError:
            logger.error("Failed to read users.json, starting with empty list")
    
    if not any(user['id'] == user_id for user in users):
        users.append({"id": user_id, "username": username if username else "ندارد"})
        try:
            with open(USERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=4)
            logger.info(f"Saved user {user_id} to users.json")
        except Exception as e:
            logger.error(f"Error saving user {user_id} to users.json: {e}")


commands = [
    telebot.types.BotCommand("start", "شروع ربات"),
]
bot.set_my_commands(commands)


bot_start_time = datetime.now(timezone('Asia/Tehran')).timestamp()

def is_message_valid(message):
    message_time = message.date
    logger.info(f"Checking message timestamp: {message_time} vs bot_start_time: {bot_start_time}")
    if message_time < bot_start_time:
        logger.warning(f"Ignoring old message from user {message.chat.id} sent at {message_time}")
        return False
    return True

def check_rate_limit(user_id):
    current_time = time()
    
    if user_id not in message_tracker:
        message_tracker[user_id] = {'count': 0, 'last_time': current_time, 'temp_block_until': 0}
    
    if current_time < message_tracker[user_id]['temp_block_until']:
        remaining = int(message_tracker[user_id]['temp_block_until'] - current_time)
        return False, f"شما به دلیل ارسال پیام زیاد تا {remaining} ثانیه نمی‌تونید پیام بفرستید 😕"
    
    if current_time - message_tracker[user_id]['last_time'] > 1:
        message_tracker[user_id]['count'] = 0
        message_tracker[user_id]['last_time'] = current_time
    
    message_tracker[user_id]['count'] += 1
    
    if message_tracker[user_id]['count'] > 2:
        message_tracker[user_id]['temp_block_until'] = current_time + 30
        return False, "شما بیش از حد پیام فرستادید! تا ۳۰ ثانیه نمی‌تونید پیام بفرستید 😕"
    
    return True, ""

def send_broadcast(message):
    if not is_message_valid(message):
        return
    user_id = message.chat.id
    if user_id not in ADMIN_USER_IDS:
        return
    users = []
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                users = json.load(f)
        except json.JSONDecodeError:
            logger.error("Failed to read users.json")
            bot.send_message(user_id, "❌ خطا در خواندن لیست کاربران!")
            return
    success_count = 0
    for user in users:
        try:
            bot.send_message(user["id"], message.text)
            success_count += 1
            sleep(0.5)
        except Exception as e:
            logger.warning(f"Failed to send broadcast to user {user['id']}: {e}")
            continue
    bot.send_message(user_id, f"پیام به {success_count} کاربر ارسال شد 📢")
    logger.info(f"Broadcast sent to {success_count} users by admin {user_id}")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not is_message_valid(message):
        return
    
    user_id = message.from_user.id
    username = message.from_user.username
    save_user(user_id, username)

    allowed, error_message = check_rate_limit(user_id)
    if not allowed:
        bot.send_message(user_id, error_message)
        return
    
    chat_id = message.chat.id
    
    # تنظیم حالت متفاوت برای ادمین‌ها
    if user_id in ADMIN_USER_IDS:
        user_data[chat_id] = {'state': 'admin_menu'}  # حالت خاص برای ادمین
    else:
        user_data[chat_id] = {'state': 'waiting_for_phone'} 

    welcome_message = (
        f"👋 سلام {message.from_user.first_name} عزیز! به ربات دریافت API تلگرام خوش آمدید!\n\n"
        "این ربات به شما کمک می‌کند تا API ID و API Hash حساب تلگرام خود را به راحتی دریافت کنید. "
        "این اطلاعات برای توسعه‌دهندگان و افرادی که می‌خواهند با API تلگرام کار کنند، مفید است.\n\n"
        "⚠️ توجه: شماره موبایل شما نزد ما محفوظ است و در هیچ کجا ذخیره نمی‌شود. "
        "فرآیند دریافت API کاملاً امن است و مستقیماً از طریق تلگرام انجام می‌شود.\n\n"
        "برای شروع، لطفاً شماره موبایل خود را به همراه کد کشور (مثال: +989123456789) ارسال کنید."
    )
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button_phone = types.KeyboardButton("اشتراک گذاری شماره موبایل 📱", request_contact=True)
    markup.add(button_phone)
    
    # اضافه کردن دکمه پیام همگانی برای ادمین
    if user_id in ADMIN_USER_IDS:
        btn_special = types.KeyboardButton("پیام همگانی 📢")
        markup.add(btn_special)
    
    bot.send_message(chat_id, welcome_message, reply_markup=markup)
    if user_id in ADMIN_USER_IDS:
        bot.send_message(chat_id, "شما ادمین هستید! می‌توانید از دکمه 'پیام همگانی 📢' برای ارسال پیام به همه کاربران استفاده کنید.")
    else:
        bot.send_message(chat_id, "لطفاً شماره موبایل خود را برای دریافت API ID و API Hash ارسال کنید "
                                   "(می‌توانید آن را تایپ کنید یا با دکمه زیر به اشتراک بگذارید):")

@bot.message_handler(content_types=['contact', 'text'], func=lambda message: user_data.get(message.chat.id, {}).get('state') == 'waiting_for_phone')
def handle_phone_number(message):
    if not is_message_valid(message):
        return
    
    user_id = message.from_user.id
    allowed, error_message = check_rate_limit(user_id)
    if not allowed:
        bot.send_message(user_id, error_message)
        return
    
    chat_id = message.chat.id
    
    if message.contact:
        phone_number = message.contact.phone_number
        if not phone_number.startswith('+'):
            phone_number = '+' + phone_number 
        bot.send_message(chat_id, f"شماره شما: `{phone_number}` دریافت شد. منتظر ارسال کد تایید از تلگرام باشید...", parse_mode='Markdown')
    elif message.text:
        phone_number = message.text.strip()

        phone_number = re.sub(r'[^\d+]', '', phone_number) 
        if not phone_number.startswith('+'):
            if phone_number.startswith('00'):
                phone_number = '+' + phone_number[2:]
            elif phone_number.startswith('0'):

                if len(phone_number) == 11 and phone_number.startswith('09'): 
                    phone_number = '+98' + phone_number[1:]
                else:
                    bot.send_message(chat_id, "فرمت شماره موبایل نامعتبر است. لطفاً شماره را با کد کشور (مثال: +989123456789) وارد کنید یا از دکمه 'اشتراک گذاری شماره موبایل' استفاده کنید.")
                    return
            else:
                bot.send_message(chat_id, "فرمت شماره موبایل نامعتبر است. لطفاً شماره را با کد کشور (مثال: +989123456789) وارد کنید یا از دکمه 'اشتراک گذاری شماره موبایل' استفاده کنید.")
                return
        
        bot.send_message(chat_id, f"شماره شما: `{phone_number}` دریافت شد. منتظر ارسال کد تایید از تلگرام باشید...", parse_mode='Markdown')
    else:
        bot.send_message(chat_id, "لطفاً شماره موبایل خود را ارسال کنید یا از دکمه 'اشتراک گذاری شماره موبایل' استفاده کنید.")
        return

    user_data[chat_id]['phone'] = phone_number
    

    with requests.Session() as req:
        try:
            login0 = req.post('https://my.telegram.org/auth/send_password', data={'phone': phone_number})
            login0.raise_for_status() 
            
            if 'Sorry, too many tries. Please try again later.' in login0.text:
                bot.send_message(chat_id, 'متاسفانه حساب شما مسدود شده است! 🚫 لطفا 8 ساعت دیگر امتحان کنید.')
                user_data.pop(chat_id, None)
                return

            login_data = login0.json()
            random_hash = login_data['random_hash']
            user_data[chat_id]['random_hash'] = random_hash
            user_data[chat_id]['state'] = 'waiting_for_code'
            
            bot.send_message(chat_id, "حالا کدی که از طرف تلگرام برای شما ارسال شده را وارد کنید. "
                                       "می‌توانید کد پیام تلگرام را هم فوروارد کنید. ✉️")
            
        except requests.exceptions.RequestException as e:
            bot.send_message(chat_id, f"مشکلی در ارتباط با سرور تلگرام پیش آمد: {e} 😞")
            user_data.pop(chat_id, None)
        except KeyError:
             bot.send_message(chat_id, "خطا در دریافت random_hash. لطفا شماره را مجددا بررسی کنید یا بعدا تلاش نمایید. 😔")
             user_data.pop(chat_id, None)


@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('state') == 'waiting_for_code')
def handle_code(message):
    if not is_message_valid(message):
        return
    
    user_id = message.from_user.id
    allowed, error_message = check_rate_limit(user_id)
    if not allowed:
        bot.send_message(user_id, error_message)
        return
    chat_id = message.chat.id
    user_info = user_data.get(chat_id)

    if not user_info or not user_info['random_hash'] or not user_info['phone']:
        bot.send_message(chat_id, "لطفاً ابتدا شماره موبایل خود را ارسال کنید. از /start استفاده کنید.")
        user_data.pop(chat_id, None) 
        return

    code = message.text.strip()
    
    code_match = re.search(r'This is your login code:\s*([a-zA-Z0-9]+)', code)
    if code_match:
        code = code_match.group(1) 
    elif re.match(r'^[a-zA-Z0-9]+$', code) and len(code) > 5 and len(code) < 15: 
        pass
    else:
        bot.send_message(chat_id, "کد وارد شده نامعتبر است. لطفاً کد صحیح را مجدداً وارد کنید یا پیام فوروارد شده را ارسال کنید. 🔢")
        return

    phone_number = user_info['phone']
    random_hash = user_info['random_hash']

    with requests.Session() as req:
        try:
            login_data = {
                'phone': phone_number,
                'random_hash': random_hash,
                'password': code
            }
            
            login = req.post('https://my.telegram.org/auth/login', data=login_data)
            login.raise_for_status() 

            apps_page = req.get('https://my.telegram.org/apps')
            apps_page.raise_for_status() 
            
            soup = BeautifulSoup(apps_page.text, 'html.parser')
            
            api_id = soup.find('label', string='App api_id:').find_next_sibling('div').select_one('span').get_text()
            api_hash = soup.find('label', string='App api_hash:').find_next_sibling('div').select_one('span').get_text()
            key = soup.find('label', string='Public keys:').find_next_sibling('div').select_one('code').get_text()
            Pc = soup.find('label', string='Production configuration:').find_next_sibling('div').select_one('strong').get_text()

            response_message = (
                "🎉 API شما با موفقیت دریافت شد!\n\n"
                f"🔑 *Api ID*: `{api_id}`\n"
                f"🔒 *Api HASH*: `{api_hash}`\n\n"
                f"🧩 *Public Key*: `{key}`\n"
                f"⚙️ *Production configuration*: `{Pc}`\n\n"
                "امیدواریم از این اطلاعات برای پروژه‌های خود استفاده مفید کنید! 😊"
            )
            bot.send_message(chat_id, response_message, parse_mode='Markdown')

        except AttributeError:
            bot.send_message(chat_id, "متاسفانه اطلاعات API یافت نشد. 🧐 احتمالاً اطلاعات وارد شده نادرست بوده یا تلگرام با خطایی مواجه شده است. لطفاً از دستور /start برای شروع مجدد استفاده کنید.")
        except requests.exceptions.RequestException as e:
            bot.send_message(chat_id, f"مشکلی در ارتباط با سرور تلگرام پیش آمد: {e} 😞. لطفاً مطمئن شوید که کد صحیح را وارد کرده‌اید و از /start برای شروع مجدد استفاده کنید.")
        finally:
            user_data.pop(chat_id, None) #

@bot.message_handler(func=lambda message: message.text == "پیام همگانی 📢")
def handle_broadcast(message):
    if not is_message_valid(message):
        return
    user_id = message.chat.id
    if user_id not in ADMIN_USER_IDS:
        bot.send_message(user_id, "این قابلیت فقط برای ادمین‌ها در دسترسه!")
        return
    logger.info(f"Broadcast initiated by admin {user_id}")
    bot.send_message(user_id, "هر پیامی که می‌خوای بنویس تا برای همه کاربران ارسال بشه 📢")
    bot.register_next_step_handler(message, send_broadcast)

@bot.message_handler(commands=['alive'])
def alive_command(message):
    """Handles the /alive command."""
    if not is_message_valid(message):
        return
    user_id = message.from_user.id
    allowed, error_message = check_rate_limit(user_id)
    if not allowed:
        bot.send_message(user_id, error_message)
        return
    
    bot.send_message(
        message.chat.id,
        "I'm alive and kicking! 🤖 DigitIDBot is here!"
    )

bot.polling(none_stop=True)