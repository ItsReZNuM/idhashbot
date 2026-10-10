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

    # Forwarded English telegram message
    msg_en = "Web login code.\nThis is your login code: aBcDeF12\nDo not give this code to anyone."
    assert extract_login_code(msg_en) == "aBcDeF12"

    # Forwarded Persian telegram message
    msg_fa = "کد ورود شما: fA123bC\nاین کد را در اختیار دیگران نگذارید."
    assert extract_login_code(msg_fa) == "fA123bC"

    # Forwarded Russian telegram message
    msg_ru = "Ваш код для входа: RuCode99\nНикому не сообщайте этот код."
    assert extract_login_code(msg_ru) == "RuCode99"


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
