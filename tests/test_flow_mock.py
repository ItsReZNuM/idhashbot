import re
import pytest
import requests
from bs4 import BeautifulSoup
from unittest.mock import MagicMock, patch
from telegram_service import send_telegram_code, login_and_get_credentials, create_telegram_app


def test_send_telegram_code_rate_limited():
    session = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = "Sorry, too many tries. Please try again later."
    session.post.return_value = mock_resp

    success, status, r_hash = send_telegram_code(session, "+989123456789")
    assert success is False
    assert status == 'rate_limited'
    assert r_hash is None


def test_send_telegram_code_success():
    session = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = '{"random_hash": "abc123random"}'
    mock_resp.json.return_value = {"random_hash": "abc123random"}
    session.post.return_value = mock_resp

    success, status, r_hash = send_telegram_code(session, "+989123456789")
    assert success is True
    assert status == 'ok'
    assert r_hash == 'abc123random'


def test_login_failed_wrong_code():
    session = MagicMock()
    login_resp = MagicMock()
    login_resp.status_code = 200
    login_resp.text = "Invalid confirmation code"
    session.post.return_value = login_resp

    success, creds, err = login_and_get_credentials(session, "+989123456789", "hash123", "wrong_code")
    assert success is False
    assert creds is None
    assert "login_failed" in err


def test_login_success_and_extract_credentials():
    session = MagicMock()
    login_resp = MagicMock()
    login_resp.status_code = 200
    login_resp.text = "true"
    session.post.return_value = login_resp

    apps_page_resp = MagicMock()
    apps_page_resp.url = "https://my.telegram.org/apps"
    apps_page_resp.text = '''
    <div class="form-group">
      <label>App api_id:</label>
      <div><span class="uneditable-input">99887766</span></div>
      <label>App api_hash:</label>
      <div><span class="uneditable-input">aabbccddeeff00112233445566778899</span></div>
    </div>
    '''
    session.get.return_value = apps_page_resp

    success, creds, err = login_and_get_credentials(session, "+989123456789", "hash123", "correct_code")
    assert success is True
    assert creds['api_id'] == "99887766"
    assert creds['api_hash'] == "aabbccddeeff00112233445566778899"
    assert err == "ok"


def test_login_success_auto_create_app():
    session = MagicMock()
    login_resp = MagicMock()
    login_resp.status_code = 200
    login_resp.text = "true"
    session.post.return_value = login_resp

    create_page_resp = MagicMock()
    create_page_resp.url = "https://my.telegram.org/apps"
    create_page_resp.text = '''
    <form action="/apps/create" method="post">
      <input type="hidden" name="hash" value="csrf_token_xyz" />
    </form>
    '''

    final_page_resp = MagicMock()
    final_page_resp.url = "https://my.telegram.org/apps"
    final_page_resp.text = '''
    <div class="form-group">
      <label>App api_id:</label>
      <div><span>11223344</span></div>
      <label>App api_hash:</label>
      <div><span>00112233445566778899aabbccddeeff</span></div>
    </div>
    '''

    # First get returns create page, second get returns final page
    session.get.side_effect = [create_page_resp, final_page_resp]

    # Post for /apps/create returns 200 without ERROR
    create_resp = MagicMock()
    create_resp.status_code = 200
    create_resp.text = "OK"

    # session.post returns login_resp on 1st call, create_resp on 2nd call
    session.post.side_effect = [login_resp, create_resp]

    success, creds, err = login_and_get_credentials(session, "+989123456789", "hash123", "code")
    assert success is True
    assert creds['api_id'] == "11223344"
    assert creds['api_hash'] == "00112233445566778899aabbccddeeff"


def test_login_app_creation_rejected_distinguished_from_not_found():
    session = MagicMock()
    login_resp = MagicMock()
    login_resp.status_code = 200
    login_resp.text = "true"

    create_page_resp = MagicMock()
    create_page_resp.url = "https://my.telegram.org/apps"
    create_page_resp.text = '''
    <form action="/apps/create" method="post">
      <input type="hidden" name="hash" value="csrf_token_xyz" />
      <input type="text" name="app_title" />
      <input type="text" name="app_shortname" />
    </form>
    '''
    session.get.return_value = create_page_resp

    create_resp = MagicMock()
    create_resp.status_code = 200
    create_resp.text = "ERROR"

    session.post.side_effect = [login_resp, create_resp]

    success, creds, err = login_and_get_credentials(session, "+989123456789", "hash123", "code")
    assert success is False
    assert creds is None
    # Must NOT be credentials_not_found! Must specifically identify app_creation_rejected
    assert err == 'app_creation_rejected'


def test_login_app_creation_still_on_create_page():
    session = MagicMock()
    login_resp = MagicMock()
    login_resp.status_code = 200
    login_resp.text = "true"

    create_page_resp = MagicMock()
    create_page_resp.url = "https://my.telegram.org/apps"
    create_page_resp.text = '''
    <form action="/apps/create" method="post">
      <input type="hidden" name="hash" value="csrf_token_xyz" />
      <input type="text" name="app_title" />
    </form>
    '''
    # Both initial get and refetched get return the create page
    session.get.return_value = create_page_resp

    create_resp = MagicMock()
    create_resp.status_code = 200
    create_resp.text = "OK"  # Claims OK, but page is still create form

    session.post.side_effect = [login_resp, create_resp]

    success, creds, err = login_and_get_credentials(session, "+989123456789", "hash123", "code")
    assert success is False
    assert creds is None
    assert err == 'app_creation_rejected'


def test_login_account_restricted_flow():
    session = MagicMock()
    login_resp = MagicMock()
    login_resp.status_code = 200
    login_resp.text = "true"
    session.post.return_value = login_resp

    restricted_page_resp = MagicMock()
    restricted_page_resp.url = "https://my.telegram.org/apps"
    restricted_page_resp.text = '''
    <div class="alert alert-danger">Your account is restricted from creating applications.</div>
    '''
    session.get.return_value = restricted_page_resp

    success, creds, err = login_and_get_credentials(session, "+989123456789", "hash123", "code")
    assert success is False
    assert creds is None
    assert err.startswith('account_restricted:')


def test_login_app_creation_modern_redesign_flow():
    session = MagicMock()
    login_resp = MagicMock()
    login_resp.status_code = 200
    login_resp.text = "true"

    fresh_page = MagicMock()
    fresh_page.url = "https://my.telegram.org/apps"
    fresh_page.text = '''
    <form class="card" id="app_create_form">
      <input type="hidden" name="hash" value="94a3fc44285fc76910"/>
      <input id="app_title" name="app_title" type="text">
      <input id="app_shortname" name="app_shortname" type="text">
    </form>
    '''

    creds_page = MagicMock()
    creds_page.url = "https://my.telegram.org/apps"
    creds_page.text = '''
    <div class="card">
      <div class="creds">
        <div class="cred">
          <div class="k">App api_id</div>
          <div class="v"><span class="vv">33445566</span></div>
        </div>
        <div class="cred">
          <div class="k">App api_hash</div>
          <div class="v masked" data-value="abcdef0123456789abcdef0123456789"></div>
        </div>
      </div>
    </div>
    '''

    create_resp = MagicMock()
    create_resp.status_code = 200
    create_resp.text = "OK"

    session.post.side_effect = [login_resp, create_resp]
    session.get.side_effect = [fresh_page, creds_page]

    success, creds, err = login_and_get_credentials(session, "+989123456789", "hash123", "code")
    assert success is True
    assert creds['api_id'] == "33445566"
    assert creds['api_hash'] == "abcdef0123456789abcdef0123456789"


def test_login_app_creation_flood_rate_limit():
    session = MagicMock()
    login_resp = MagicMock()
    login_resp.status_code = 200
    login_resp.text = "true"

    fresh_page = MagicMock()
    fresh_page.url = "https://my.telegram.org/apps"
    fresh_page.text = '''
    <form class="card" id="app_create_form">
      <input type="hidden" name="hash" value="94a3fc44285fc76910"/>
      <input id="app_title" name="app_title" type="text">
      <input id="app_shortname" name="app_shortname" type="text">
    </form>
    '''

    create_resp = MagicMock()
    create_resp.status_code = 400
    create_resp.json.return_value = {"text": "Too many attempts. Please try again later.", "field": False}

    session.post.side_effect = [login_resp, create_resp]
    session.get.return_value = fresh_page

    success, creds, err = login_and_get_credentials(session, "+989123456789", "hash123", "code")
    assert success is False
    assert creds is None
    assert err == "app_creation_flood"


