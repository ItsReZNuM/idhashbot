# telegram_service.py
"""
Service module for interacting with my.telegram.org.
Ports robust multi-layered scraping and app creation logic from ApiIDHash.
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
    """Normalize phone number and validate international format."""
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
    """
    Extract Telegram verification code from raw string or forwarded system message.
    Handles codes containing letters, digits, underscores, and hyphens (e.g. QBg-V-T9a7c).
    """
    if not code_input:
        return ""

    # English Telegram system message pattern (e.g. This is your login code: \n QBg-V-T9a7c)
    code_match = re.search(r'This is your login code:\s*([a-zA-Z0-9_\-]+)', code_input, re.IGNORECASE)
    if code_match:
        return code_match.group(1).strip()

    # Persian Telegram system message pattern
    fa_match = re.search(r'کد ورود شما:\s*([a-zA-Z0-9_\-]+)', code_input)
    if fa_match:
        return fa_match.group(1).strip()

    # Russian Telegram system message pattern
    ru_match = re.search(r'Ваш код для входа:\s*([a-zA-Z0-9_\-]+)', code_input, re.IGNORECASE)
    if ru_match:
        return ru_match.group(1).strip()

    # Fallback: search lines for a standalone token matching telegram code structure (6-25 characters)
    for line in code_input.splitlines():
        line = line.strip()
        if re.fullmatch(r'[a-zA-Z0-9_\-]{6,25}', line):
            return line

    return code_input.strip()


def extract_credentials(html: str, soup: BeautifulSoup) -> tuple[str | None, str | None, str | None, str | None]:
    """
    Robust multi-layered extraction of api_id, api_hash, public_key, and prod_config.
    Layer 1: Flexible DOM search across label tags and parent containers.
    Layer 2: Search elements with uneditable/selectable classes or attributes.
    Layer 3: Direct regex fallbacks on the raw HTML.
    """
    api_id = None
    api_hash = None
    public_key = None
    prod_config = None

    # Layer 1: Flexible DOM search across label tags and parent containers
    labels = soup.find_all(['label', 'span', 'strong', 'td', 'th'])
    for el in labels:
        txt = el.get_text(strip=True).lower()
        parent = el.find_parent(['div', 'tr', 'fieldset']) or el

        if 'api_id' in txt and not api_id:
            val_el = parent.find(['span', 'input', 'strong', 'code'])
            if val_el:
                val = val_el.get_text(strip=True) or (val_el.get('value') or '')
                m = re.search(r'\b\d{5,12}\b', val)
                if m:
                    api_id = m.group(0)

        elif 'api_hash' in txt and not api_hash:
            val_el = parent.find(['span', 'input', 'strong', 'code'])
            if val_el:
                val = val_el.get_text(strip=True) or (val_el.get('value') or '')
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

    # Layer 2: Elements with uneditable or selectable classes/attributes
    if not (api_id and api_hash):
        selectable = soup.find_all(lambda tag: (
            tag.name in ['span', 'input'] and (
                'this.select()' in (tag.get('onclick') or '')
                or 'uneditable-input' in (tag.get('class') or [])
                or 'form-control' in (tag.get('class') or [])
            )
        ))
        for item in selectable:
            val = item.get_text(strip=True) or (item.get('value') or '')
            if not api_id and re.fullmatch(r'\d{5,12}', val):
                api_id = val
            elif not api_hash and re.fullmatch(r'[0-9a-fA-F]{32}', val):
                api_hash = val

    # Layer 3: Direct regex fallbacks on raw HTML content
    if not api_id:
        m_id = re.search(r'api_id.*?(\b\d{5,12}\b)', html, re.IGNORECASE | re.DOTALL)
        if m_id:
            api_id = m_id.group(1)
        else:
            m_id2 = re.search(r'app[_-]?id.*?(\b\d{5,12}\b)', html, re.IGNORECASE | re.DOTALL)
            if m_id2:
                api_id = m_id2.group(1)

    if not api_hash:
        m_hash = re.search(r'api_hash.*?(\b[0-9a-fA-F]{32}\b)', html, re.IGNORECASE | re.DOTALL)
        if m_hash:
            api_hash = m_hash.group(1)
        else:
            m_hash2 = re.search(r'app[_-]?hash.*?(\b[0-9a-fA-F]{32}\b)', html, re.IGNORECASE | re.DOTALL)
            if m_hash2:
                api_hash = m_hash2.group(1)

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
    """Automatically create a Telegram application if the account has none."""
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
        logger.error(f"Error creating Telegram app: {e}")
        return False, str(e)


def send_telegram_code(session: requests.Session, phone_number: str) -> tuple[bool, str, str | None]:
    """
    Request confirmation code from my.telegram.org/auth/send_password.
    Returns: (success: bool, status_or_error: str, random_hash: str | None)
    """
    try:
        send_resp = session.post(
            'https://my.telegram.org/auth/send_password',
            data={'phone': phone_number},
            headers={'X-Requested-With': 'XMLHttpRequest'},
            timeout=15
        )
    except requests.RequestException as e:
        logger.error(f"Network error in send_password: {e}")
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
        logger.error(f"Error parsing send_password response: {e} | Raw: {send_resp.text[:100]}")
        return False, 'parse_error', None


def login_and_get_credentials(
    session: requests.Session,
    phone_number: str,
    random_hash: str,
    code: str
) -> tuple[bool, dict | None, str]:
    """
    Authenticate confirmation code at my.telegram.org and extract API credentials.
    Returns: (success: bool, data_dict_or_None: dict | None, error_code_or_msg: str)
    """
    try:
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
        logger.info(f"Telegram auth/login response status: {login_resp.status_code}, content: {login_text[:100]}")

        if login_resp.status_code != 200 or login_text.lower() != 'true':
            err_msg = login_text if login_text else f"HTTP {login_resp.status_code}"
            return False, None, f"login_failed:{err_msg}"

        # Access /apps page
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

        # If application needs to be created first
        if soup.find('form', action=re.compile(r'/apps/create')):
            logger.info("No Telegram application found for account. Creating one automatically...")
            created, reason = create_telegram_app(session, soup)
            if not created:
                if reason == 'rejected':
                    return False, None, 'app_creation_rejected'
                return False, None, f"app_creation_failed:{reason}"

            # Refetch /apps page after creating application
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
            logger.warning(f"Could not extract API credentials from page. Snippet: {apps_page.text[:300]}")
            return False, None, 'credentials_not_found'

        logger.info("API credentials extracted successfully.")
        return True, {
            'api_id': api_id,
            'api_hash': api_hash,
            'public_key': key,
            'prod_config': pc
        }, 'ok'

    except Exception as e:
        logger.error(f"Unexpected exception in login_and_get_credentials: {e}", exc_info=True)
        return False, None, f"error:{e}"
