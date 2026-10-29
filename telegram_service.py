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
    Layer 0: Modern Telegram UI (.creds, .cred with .k/.v and data-value / data-copy).
    Layer 1: Flexible DOM search across label tags and parent containers.
    Layer 2: Search elements with uneditable/selectable classes or data-copy attributes.
    Layer 3: Direct regex fallbacks on the raw HTML.
    """
    api_id = None
    api_hash = None
    public_key = None
    prod_config = None

    # Layer 0: Modern Telegram UI (.creds with .cred items)
    for cred in soup.find_all(['div', 'section'], class_='cred'):
        k_el = cred.find(class_='k')
        if not k_el:
            continue
        k_text = k_el.get_text(strip=True).lower()
        v_el = cred.find(class_='v')
        candidates = []
        if v_el:
            if v_el.get('data-value'):
                candidates.append(v_el['data-value'].strip())
            vv = v_el.find(class_='vv')
            if vv:
                candidates.append(vv.get_text(strip=True))
            candidates.append(v_el.get_text(strip=True))
        for btn in cred.find_all(attrs={'data-copy': True}):
            candidates.append(btn['data-copy'].strip())

        for val in candidates:
            if 'api_id' in k_text and not api_id:
                m = re.search(r'\b\d{5,12}\b', val)
                if m:
                    api_id = m.group(0)
            elif 'api_hash' in k_text and not api_hash:
                m = re.search(r'\b[0-9a-fA-F]{32}\b', val)
                if m:
                    api_hash = m.group(0)

    # Modern Telegram UI: MTProto servers
    for srv in soup.find_all(class_='server'):
        if 'production' in srv.get_text().lower():
            addr_m = re.search(r'Address\s*([0-9.]+:\d+)', srv.get_text())
            if addr_m:
                prod_config = addr_m.group(1)
            else:
                dd = srv.find('dd')
                if dd and ':' in dd.get_text():
                    prod_config = dd.get_text(strip=True)
            key_pre = srv.find('pre')
            if key_pre and 'BEGIN RSA PUBLIC KEY' in key_pre.get_text():
                public_key = key_pre.get_text(strip=True)

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

    # Layer 2: Elements with uneditable or selectable classes, data-copy, or data-value
    if not (api_id and api_hash):
        for el in soup.find_all(attrs={'data-copy': True}):
            val = el['data-copy'].strip()
            if not api_id and re.fullmatch(r'\d{5,12}', val):
                api_id = val
            elif not api_hash and re.fullmatch(r'[0-9a-fA-F]{32}', val):
                api_hash = val
        for el in soup.find_all(attrs={'data-value': True}):
            val = el['data-value'].strip()
            if not api_id and re.fullmatch(r'\d{5,12}', val):
                api_id = val
            elif not api_hash and re.fullmatch(r'[0-9a-fA-F]{32}', val):
                api_hash = val

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


def is_app_create_page(soup: BeautifulSoup) -> bool:
    """Check if the current page is the Telegram app creation form."""
    if soup.find('form', id='app_create_form'):
        return True
    if soup.find('form', id='app_edit_form') or soup.find(class_='creds'):
        return False
    if soup.find('form', action=re.compile(r'create', re.IGNORECASE)):
        return True
    if soup.find('input', {'name': 'app_title'}):
        return True
    if soup.find('input', {'name': 'app_shortname'}):
        return True
    return False


def is_account_restricted_page(html: str, soup: BeautifulSoup) -> tuple[bool, str]:
    """Check if the page indicates that the account is restricted by Telegram."""
    alert = soup.find(['div', 'span', 'p'], class_=re.compile(r'alert-danger|alert-error|error-msg|danger', re.IGNORECASE))
    if alert:
        text = alert.get_text(strip=True)
        if text:
            return True, text

    restriction_patterns = [
        r'sorry,?\s*too\s*many\s*tries',
        r'flood_wait',
        r'account\s*(?:is\s*)?restricted',
        r'you\s*can[\'’]?t\s*create\s*(?:an?\s*)?application',
    ]
    for pattern in restriction_patterns:
        m = re.search(pattern, html, re.IGNORECASE)
        if m:
            return True, m.group(0)

    return False, ""


def create_telegram_app(session: requests.Session, soup: BeautifulSoup) -> tuple[bool, str]:
    """Automatically create a Telegram application if the account has none."""
    hash_input = soup.find('input', {'name': 'hash'})
    if not hash_input or not hash_input.get('value'):
        return False, "csrf_hash_missing"

    csrf_hash = hash_input['value']
    rand_chars = ''.join(random.choices(string.ascii_lowercase, k=4))
    rand_digits = ''.join(random.choices(string.digits, k=4))
    rand_suffix = f"{rand_chars}{rand_digits}"

    # Telegram strictly forbids the word 'Telegram' and special characters in app names
    app_title = f"ClientApp {rand_suffix.capitalize()}"
    app_shortname = f"devapp{rand_suffix}"

    payload = {
        'hash': csrf_hash,
        'app_title': app_title,
        'app_shortname': app_shortname,
        'app_url': '',
        'app_platform': 'desktop',
        'app_desc': 'Personal MTProto client for API development',
    }

    create_headers = dict(BROWSER_HEADERS)
    create_headers.update({
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://my.telegram.org/apps',
        'Origin': 'https://my.telegram.org',
    })

    try:
        resp = session.post(
            'https://my.telegram.org/apps/create',
            data=payload,
            headers=create_headers,
            timeout=15
        )
        resp_text = resp.text.strip()
        logger.info(f"Telegram apps/create response status: {resp.status_code}, content: {resp_text[:120]}")

        if resp.status_code == 200:
            if resp_text.upper() == 'ERROR' or 'ERROR' in resp_text:
                return False, "rejected"
            if 'FLOOD' in resp_text.upper():
                return False, "flood_wait"
            return True, "ok"
        else:
            try:
                err_data = resp.json()
                err_text = err_data.get('text', '')
                if 'flood' in err_text.lower():
                    return False, "flood_wait"
                return False, err_text or f"HTTP {resp.status_code}"
            except Exception:
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

    err_text = ""
    try:
        data = send_resp.json()
        if isinstance(data, dict):
            err_text = data.get('text', '')
            random_hash = data.get('random_hash')
            if random_hash:
                return True, 'ok', random_hash
    except Exception:
        err_text = send_resp.text

    check_text = (err_text or send_resp.text).lower()
    if 'too many tries' in check_text or 'flood' in check_text:
        return False, 'rate_limited', None

    if err_text:
        return False, err_text, None

    return False, f"HTTP {send_resp.status_code}" if send_resp.status_code != 200 else 'parse_error', None


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

        if login_resp.status_code != 200 or login_text.lower() not in ('true', ''):
            err_msg = login_text
            try:
                err_data = login_resp.json()
                if isinstance(err_data, dict) and err_data.get('text'):
                    err_msg = err_data['text']
            except Exception:
                pass
            err_msg = err_msg if err_msg else f"HTTP {login_resp.status_code}"
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

        if '/auth' in apps_page.url or 'my_login_form' in apps_page.text or 'stage_phone' in apps_page.text:
            return False, None, 'session_expired'

        soup = BeautifulSoup(apps_page.text, 'html.parser')

        # Check if application needs to be created first
        if is_app_create_page(soup):
            logger.info("No Telegram application found for account. Creating one automatically...")
            created, reason = create_telegram_app(session, soup)
            if not created:
                logger.warning(f"Telegram app creation failed: {reason}")
                if reason == 'rejected':
                    return False, None, 'app_creation_rejected'
                if reason == 'flood_wait':
                    return False, None, 'app_creation_flood'
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

            # If still on the create page, creation did not take effect on the server
            if is_app_create_page(soup):
                logger.warning("Still on app create page after creation attempt. Account requires manual app creation.")
                return False, None, 'app_creation_rejected'

        # Check if account has restrictions or errors on page
        is_restricted, rest_detail = is_account_restricted_page(apps_page.text, soup)
        if is_restricted:
            logger.warning(f"Account restricted on my.telegram.org: {rest_detail}")
            return False, None, f"account_restricted:{rest_detail}"

        api_id, api_hash, key, pc = extract_credentials(apps_page.text, soup)

        if not api_id or not api_hash:
            if is_app_create_page(soup):
                return False, None, 'app_creation_rejected'
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
