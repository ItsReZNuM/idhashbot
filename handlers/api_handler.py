# handlers/api_handler.py
import requests
from bs4 import BeautifulSoup
import re
from utils import is_message_valid, check_rate_limit

def register_api_handlers(bot, user_data):
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
                        bot.send_message(chat_id, "فرمت شماره موبایل نامعتبر است. لطفاً شماره را با کد کشور (مثال: +989123456789) وارد کنید.")
                        return
                else:
                    bot.send_message(chat_id, "فرمت شماره موبایل نامعتبر است. لطفاً شماره را با کد کشور (مثال: +989123456789) وارد کنید.")
                    return
            
            bot.send_message(chat_id, f"شماره شما: `{phone_number}` دریافت شد. منتظر ارسال کد تایید از تلگرام باشید...", parse_mode='Markdown')
        else:
            bot.send_message(chat_id, "لطفاً شماره موبایل خود را ارسال کنید.")
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
                
                bot.send_message(chat_id, "حالا کدی که از طرف تلگرام برای شما ارسال شده را وارد کنید. می‌توانید کد پیام تلگرام را هم فوروارد کنید. ✉️")
                
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

        if not user_info or 'random_hash' not in user_info or 'phone' not in user_info:
            bot.send_message(chat_id, "لطفاً ابتدا شماره موبایل خود را ارسال کنید. از /start استفاده کنید.")
            user_data.pop(chat_id, None) 
            return

        code = message.text.strip()
        
        code_match = re.search(r'This is your login code:\s*([a-zA-Z0-9]+)', code)
        if code_match:
            code = code_match.group(1) 
        elif not (re.match(r'^[a-zA-Z0-9]+$', code) and 5 < len(code) < 15): 
            bot.send_message(chat_id, "کد وارد شده نامعتبر است. لطفاً کد صحیح را مجدداً وارد کنید یا پیام فوروارد شده را ارسال کنید. 🔢")
            return

        phone_number = user_info['phone']
        random_hash = user_info['random_hash']

        with requests.Session() as req:
            try:
                login_data = {'phone': phone_number, 'random_hash': random_hash, 'password': code}
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
                user_data.pop(chat_id, None)