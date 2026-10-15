import re
import pytest
from bs4 import BeautifulSoup
from telegram_service import (
    normalize_phone_number,
    extract_login_code,
    extract_credentials,
    BROWSER_HEADERS,
)


def test_normalize_phone_number():
    # Iranian numbers
    assert normalize_phone_number("+989123456789") == "+989123456789"
    assert normalize_phone_number("09123456789") == "+989123456789"
    assert normalize_phone_number("00989123456789") == "+989123456789"
    assert normalize_phone_number(" 989123456789 ") == "+989123456789"
    assert normalize_phone_number("+98 (912) 345-6789") == "+989123456789"

    # Russian numbers
    assert normalize_phone_number("+79123456789") == "+79123456789"
    assert normalize_phone_number("0079123456789") == "+79123456789"

    # US / International numbers
    assert normalize_phone_number("+12025550143") == "+12025550143"

    # Invalid numbers
    assert normalize_phone_number("123") is None
    assert normalize_phone_number("not_a_phone") is None
    assert normalize_phone_number("") is None
    assert normalize_phone_number(None) is None


def test_extract_login_code():
    # Direct code
    assert extract_login_code("ABC123xyz") == "ABC123xyz"
    assert extract_login_code("  code456  ") == "code456"
    assert extract_login_code("QBg-V-T9a7c") == "QBg-V-T9a7c"

    # Forwarded English telegram message with hyphens and newlines
    msg_en_hyphens = """Web login code. Dear User, we received a request from your account to log in on my.telegram.org. This is your login code:
QBg-V-T9a7c

Do not give this code to anyone, even if they say they're from Telegram!"""
    assert extract_login_code(msg_en_hyphens) == "QBg-V-T9a7c"

    # Forwarded English telegram message
    msg_en = "Web login code.\nThis is your login code: aBcDeF12\nDo not give this code to anyone."
    assert extract_login_code(msg_en) == "aBcDeF12"

    # Forwarded Persian telegram message
    msg_fa = "کد ورود شما:\nfA-123-bC\nاین کد را در اختیار دیگران نگذارید."
    assert extract_login_code(msg_fa) == "fA-123-bC"

    # Forwarded Russian telegram message
    msg_ru = "Ваш код для входа:\nRu-Code_99\nНикому не сообщайте этот код."
    assert extract_login_code(msg_ru) == "Ru-Code_99"


def test_extract_credentials_standard_markup():
    html = '''
    <div class="form-group">
      <label for="app_id" class="col-md-3 control-label">App api_id:</label>
      <div class="col-md-9">
        <span class="form-control input-xlarge uneditable-input" onclick="this.select();"><strong>1234567</strong></span>
      </div>
    </div>
    <div class="form-group">
      <label for="app_hash" class="col-md-3 control-label">App api_hash:</label>
      <div class="col-md-9">
        <span class="form-control input-xlarge uneditable-input" onclick="this.select();">0123456789abcdef0123456789abcdef</span>
      </div>
    </div>
    <div class="form-group">
      <label class="col-md-3 control-label">Public keys:</label>
      <div class="col-md-9"><code>-----BEGIN RSA PUBLIC KEY-----xyz-----END RSA PUBLIC KEY-----</code></div>
    </div>
    <div class="form-group">
      <label class="col-md-3 control-label">Production configuration:</label>
      <div class="col-md-9"><strong>149.154.167.50:443</strong></div>
    </div>
    '''
    soup = BeautifulSoup(html, 'html.parser')
    api_id, api_hash, key, pc = extract_credentials(html, soup)
    assert api_id == '1234567'
    assert api_hash == '0123456789abcdef0123456789abcdef'
    assert 'RSA PUBLIC KEY' in key
    assert pc == '149.154.167.50:443'


def test_extract_credentials_custom_markup():
    html = '''
    <div>
      <label>App api_id: </label>
      <div><input type="text" value="98765432" /></div>
      <label>App api_hash:</label>
      <div><span>abcdef0123456789abcdef0123456789</span></div>
    </div>
    '''
    soup = BeautifulSoup(html, 'html.parser')
    api_id, api_hash, key, pc = extract_credentials(html, soup)
    assert api_id == '98765432'
    assert api_hash == 'abcdef0123456789abcdef0123456789'
    assert key is None
    assert pc is None


def test_extract_credentials_regex_fallback():
    html = '''
    Some irregular raw markup api_id: 55443322 and api_hash: fedcba9876543210fedcba9876543210
    '''
    soup = BeautifulSoup(html, 'html.parser')
    api_id, api_hash, key, pc = extract_credentials(html, soup)
    assert api_id == '55443322'
    assert api_hash == 'fedcba9876543210fedcba9876543210'


def test_browser_headers():
    assert 'User-Agent' in BROWSER_HEADERS
    assert 'Accept' in BROWSER_HEADERS
    assert BROWSER_HEADERS['Origin'] == 'https://my.telegram.org'


def test_is_app_create_page():
    from telegram_service import is_app_create_page

    # Standard form with app_title and app_shortname
    html1 = '<form action="/apps/create"><input name="app_title" /><input name="app_shortname" /></form>'
    assert is_app_create_page(BeautifulSoup(html1, 'html.parser')) is True

    # Form with action="create"
    html2 = '<form action="create"><input name="hash" value="xyz" /></form>'
    assert is_app_create_page(BeautifulSoup(html2, 'html.parser')) is True

    # Page with only input name="app_title"
    html3 = '<div><input name="app_title" value="" /></div>'
    assert is_app_create_page(BeautifulSoup(html3, 'html.parser')) is True

    # Page with credentials only (not create page)
    html4 = '<div class="form-group"><label>App api_id:</label><span>12345</span></div>'
    assert is_app_create_page(BeautifulSoup(html4, 'html.parser')) is False


def test_is_account_restricted_page():
    from telegram_service import is_account_restricted_page

    # Alert danger box
    html1 = '<div class="alert alert-danger">Sorry, you cannot create an application at this time.</div>'
    restricted, detail = is_account_restricted_page(html1, BeautifulSoup(html1, 'html.parser'))
    assert restricted is True
    assert "Sorry" in detail

    # Flood wait text
    html2 = '<p>FLOOD_WAIT_18000</p>'
    restricted, detail = is_account_restricted_page(html2, BeautifulSoup(html2, 'html.parser'))
    assert restricted is True

    # Normal page
    html3 = '<div><p>Welcome to developer tools</p></div>'
    restricted, detail = is_account_restricted_page(html3, BeautifulSoup(html3, 'html.parser'))
    assert restricted is False
    assert detail == ""


def test_create_telegram_app_payload_sanitization():
    from unittest.mock import MagicMock
    from telegram_service import create_telegram_app

    session = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = "OK"
    session.post.return_value = mock_resp

    soup = BeautifulSoup('<form action="/apps/create"><input type="hidden" name="hash" value="csrf123" /></form>', 'html.parser')
    success, reason = create_telegram_app(session, soup)

    assert success is True
    assert reason == "ok"

    # Verify posted payload
    call_args = session.post.call_args
    assert call_args is not None
    posted_data = call_args[1]['data']
    posted_headers = call_args[1]['headers']

    # Must NOT contain the word 'telegram' in title or shortname
    assert 'telegram' not in posted_data['app_title'].lower()
    assert 'telegram' not in posted_data['app_shortname'].lower()

    # Shortname must be alphanumeric lowercase
    assert re.match(r'^[a-z0-9]{5,32}$', posted_data['app_shortname'])

    # Must send AJAX header
    assert posted_headers.get('X-Requested-With') == 'XMLHttpRequest'

