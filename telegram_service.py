# telegram_service.py
"""
ماژول اختصاصی ارتباط با سرورهای رسمی my.telegram.org
الهام‌گرفته و کاملاً هماهنگ با اسکریپت ApiIDHash
"""

import re
import random
import string
import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
    'Origin': 'https://my.telegram.org',
    'Referer': 'https://my.telegram.org/auth',
}


def normalize_phone_number(phone_input: str) -> str | None:
    """شماره تلفن را استانداردسازی کرده و صحت فرمت بین‌المللی آن را بررسی می‌کند."""
    if not phone_input:
        return None

    cleaned = re.sub(r'[\s\-()]', '', phone_input.strip())

    if cleaned.startswith('00'):
        cleaned = '+' + cleaned[2:]
    elif cleaned.startswith('09') and len(cleaned) == 11:
        cleaned = '+98' + cleaned[1:]
    elif not cleaned.startswith('+'):
        cleaned = '+' + cleaned

    if re.match(r'^\+\d{7,15}$', cleaned):
        return cleaned
    return None


def extract_login_code(code_input: str) -> str:
    """کد ورود ارسالی تلگرام را از پیام خام یا پیام فوروارد شده استخراج می‌کند."""
    if not code_input:
        return ""

    # قالب انگلیسی پیام تلگرام
    code_match = re.search(r'This is your login code:\s*([a-zA-Z0-9]+)', code_input, re.IGNORECASE)
    if code_match:
        return code_match.group(1).strip()

    # قالب فارسی پیام تلگرام
    fa_match = re.search(r'کد ورود شما:\s*([a-zA-Z0-9]+)', code_input)
    if fa_match:
        return fa_match.group(1).strip()

    # قالب روسی پیام تلگرام
    ru_match = re.search(r'Ваш код для входа:\s*([a-zA-Z0-9]+)', code_input, re.IGNORECASE)
    if ru_match:
        return ru_match.group(1).strip()

    return code_input.strip()


def extract_credentials(html: str, soup: BeautifulSoup) -> tuple[str | None, str | None, str | None, str | None]:
    """
    استخراج چندلایه و مقاوم API ID، API Hash، کلید عمومی و تنظیمات سرور.
    (دقیقاً منطبق بر لایه‌های استخراج ApiIDHash)
    """
    api_id = None
    api_hash = None
    public_key = None
    prod_config = None

    # لایه ۱: جستجوی منعطف تگ‌های label، span، strong و غیره
    labels = soup.find_all(['label', 'span', 'strong', 'td', 'th'])
    for el in labels:
        txt = el.get_text(strip=True).lower()
        parent = el.find_parent(['div', 'tr', 'fieldset']) or el

        if 'api_id' in txt and not api_id:
            val_el = parent.find(['span', 'input', 'strong', 'code'])
            if val_el:
                val = val_el.get_text(strip=True) or val_el.get('value', '')
                m = re.search(r'\b\d{5,12}\b', val)
                if m:
                    api_id = m.group(0)

        elif 'api_hash' in txt and not api_hash:
            val_el = parent.find(['span', 'input', 'strong', 'code'])
            if val_el:
                val = val_el.get_text(strip=True) or val_el.get('value', '')
                m = re.search(r'\b[0-9a-fA-F]{32}\b', val)
                if m:
                    api_hash = m.group(0)

        elif 'public key' in txt and not public_key:
            val_el = parent.find(['code', 'pre', 'span'])
            if val_el:
                public_key = val_el.get_text(strip=True)

        elif 'production configuration' in txt and not prod_config:
            val_el = parent.find(['strong', 'code', 'span'])
            if val_el:
                prod_config = val_el.get_text(strip=True)

    # لایه ۲: عناصر دارای استایل‌های uneditable یا selectable
    if not (api_id and api_hash):
        selectable = soup.find_all(lambda tag: (
            tag.name in ['span', 'input'] and (
                'this.select()' in tag.get('onclick', '')
                or 'uneditable-input' in tag.get('class', [])
                or 'form-control' in tag.get('class', [])
            )
        ))
        for item in selectable:
            val = item.get_text(strip=True) or item.get('value', '')
            if not api_id and re.fullmatch(r'\d{5,12}', val):
                api_id = val
            elif not api_hash and re.fullmatch(r'[0-9a-fA-F]{32}', val):
                api_hash = val

    # لایه ۳: الگوهای منظم (Regex Fallback) مستقیم روی محتوای متنی HTML
    if not api_id:
        m_id = re.search(r'api_id.*?(\b\d{5,12}\b)', html, re.IGNORECASE | re.DOTALL)
        if m_id:
            api_id = m_id.group(1)

    if not api_hash:
        m_hash = re.search(r'api_hash.*?(\b[0-9a-fA-F]{32}\b)', html, re.IGNORECASE | re.DOTALL)
        if m_hash:
            api_hash = m_hash.group(1)

    if not public_key:
        m_key = re.search(
            r'Public\s*keys?:.*?(-----BEGIN[^-]+-----.*?-----END[^-]+-----|<code[^>]*>(.*?)</code>)',
            html, re.IGNORECASE | re.DOTALL
        )
        if m_key:
            public_key = (m_key.group(1) or m_key.group(2)).strip()
            public_key = re.sub(r'<[^>]+>', '', public_key)

    if not prod_config:
        m_prod = re.search(r'Production\s*configuration:.*?<strong[^>]*>(.*?)</strong>', html, re.IGNORECASE | re.DOTALL)
        if m_prod:
            prod_config = m_prod.group(1).strip()

    return api_id, api_hash, public_key, prod_config


def create_telegram_app(session: requests.Session, soup: BeautifulSoup) -> tuple[bool, str]:
    """در صورتی که حسابی فاقد اپلیکیشن باشد، به صورت خودکار یک اپلیکیشن ثبت می‌کند."""
    hash_input = soup.find('input', {'name': 'hash'})
    if not hash_input or not hash_input.get('value'):
        return False, "csrf_hash_missing"

    csrf_hash = hash_input['value']
    rand_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    app_title = f"MyTelegramApp_{rand_suffix}"
    app_shortname = f"app{rand_suffix}"

    payload = {
        'hash': csrf_hash,
        'app_title': app_title,
        'app_shortname': app_shortname,
        'app_url': 'https://telegram.org',
        'app_platform': 'desktop',
        'app_desc': 'Personal Telegram MTProto Developer Client',
    }

    create_headers = dict(BROWSER_HEADERS)
    create_headers['Content-Type'] = 'application/x-www-form-urlencoded'
    create_headers['Referer'] = 'https://my.telegram.org/apps'

    try:
        resp = session.post(
            'https://my.telegram.org/apps/create',
            data=payload,
            headers=create_headers,
            timeout=15
        )
        if resp.status_code == 200:
            if 'ERROR' in resp.text:
                return False, "rejected"
            return True, "ok"
        else:
            return False, f"HTTP {resp.status_code}"
    except Exception as e:
        logger.error(f"خطا در ساخت خودکار اپلیکیشن تلگرام: {e}")
        return False, str(e)


def send_telegram_code(session: requests.Session, phone_number: str) -> tuple[bool, str, str | None]:
    """
    درخواست ارسال کد تأیید ورود از سرور my.telegram.org
    خروجی: (موفقیت، وضعیت/پیام خطا، random_hash)
    """
    try:
        send_resp = session.post(
            'https://my.telegram.org/auth/send_password',
            data={'phone': phone_number},
            headers={'X-Requested-With': 'XMLHttpRequest'},
            timeout=15
        )
    except requests.RequestException as e:
        logger.error(f"خطای شبکه در send_password: {e}")
        return False, f"network_error:{e}", None

    if 'Sorry, too many tries. Please try again later.' in send_resp.text:
        return False, 'rate_limited', None

    try:
        send_data = send_resp.json()
        random_hash = send_data.get('random_hash')
        if not random_hash:
            return False, 'parse_error', None
        return True, 'ok', random_hash
    except Exception as e:
        logger.error(f"خطای پردازش پاسخ send_password: {e} | متن پاسخ: {send_resp.text[:100]}")
        return False, 'parse_error', None


def login_and_get_credentials(
    session: requests.Session,
    phone_number: str,
    random_hash: str,
    code: str
) -> tuple[bool, dict | None, str]:
    """
    احراز هویت کد در my.telegram.org و دریافت اعتبارنامه‌های API ID و API Hash
    خروجی: (موفقیت، دیکشنری اطلاعات یا None، کد یا پیام خطا)
    """
    login_data = {
        'phone': phone_number,
        'random_hash': random_hash,
        'password': code,
        'remember': '1'
    }

    try:
        login_resp = session.post(
            'https://my.telegram.org/auth/login',
            data=login_data,
            headers={'X-Requested-With': 'XMLHttpRequest'},
            timeout=15
        )
    except requests.RequestException as e:
        return False, None, f"network_error:{e}"

    login_text = login_resp.text.strip()
    if login_resp.status_code != 200 or login_text.lower() != 'true':
        err_msg = login_text if login_text else f"HTTP {login_resp.status_code}"
        return False, None, f"login_failed:{err_msg}"

    # دسترسی به صفحه اپلیکیشن‌ها
    try:
        apps_page = session.get(
            'https://my.telegram.org/apps',
            headers={'Referer': 'https://my.telegram.org/'},
            timeout=15
        )
    except requests.RequestException as e:
        return False, None, f"network_error:{e}"

    if '/auth' in apps_page.url or 'my_login_form' in apps_page.text:
        return False, None, 'session_expired'

    soup = BeautifulSoup(apps_page.text, 'html.parser')

    # در صورت نیاز به ساخت برنامه جدید
    if soup.find('form', action=re.compile(r'/apps/create')):
        created, reason = create_telegram_app(session, soup)
        if not created:
            if reason == 'rejected':
                return False, None, 'app_creation_rejected'
            return False, None, f"app_creation_failed:{reason}"

        # دریافت مجدد صفحه پس از ساخت اپلیکیشن
        try:
            apps_page = session.get(
                'https://my.telegram.org/apps',
                headers={'Referer': 'https://my.telegram.org/'},
                timeout=15
            )
            soup = BeautifulSoup(apps_page.text, 'html.parser')
        except requests.RequestException as e:
            return False, None, f"network_error:{e}"

    api_id, api_hash, key, pc = extract_credentials(apps_page.text, soup)

    if not api_id or not api_hash:
        return False, None, 'credentials_not_found'

    return True, {
        'api_id': api_id,
        'api_hash': api_hash,
        'public_key': key,
        'prod_config': pc
    }, 'ok'
