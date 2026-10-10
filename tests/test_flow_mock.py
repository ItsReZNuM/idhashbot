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
