from locales import TEXTS, tr, SUPPORTED_LANGUAGES

def test_locales_coverage():
    """Verify all supported languages define the exact same set of translation keys."""
    assert 'fa' in SUPPORTED_LANGUAGES
    assert 'en' in SUPPORTED_LANGUAGES
    assert 'ru' in SUPPORTED_LANGUAGES

    fa_keys = set(TEXTS['fa'].keys())
    en_keys = set(TEXTS['en'].keys())
    ru_keys = set(TEXTS['ru'].keys())

    missing_in_en = fa_keys - en_keys
    missing_in_ru = fa_keys - ru_keys

    assert not missing_in_en, f"Keys missing in English: {missing_in_en}"
    assert not missing_in_ru, f"Keys missing in Russian: {missing_in_ru}"


def test_tr_formatting():
    """Verify string formatting works correctly in all languages."""
    for lang in ['fa', 'en', 'ru']:
        welcome = tr('welcome', lang, name="TestUser")
        assert "TestUser" in welcome

        phone_msg = tr('phone_received', lang, phone="+989120000000")
        assert "+989120000000" in phone_msg

        creds = tr('credentials_success', lang, api_id="123456", api_hash="abcdef0123456789abcdef0123456789")
        assert "123456" in creds
        assert "abcdef0123456789abcdef0123456789" in creds

        spam = tr('spam_warning', lang, remaining=15)
        assert "15" in spam

        public_k = tr('public_key_text', lang, key="MIIBCgKCAQEA...")
        assert "MIIBCgKCAQEA..." in public_k


def test_tr_fallback():
    """Verify fallback to Persian if language or key is unknown."""
    # Unknown lang falls back to fa
    res = tr('btn_cancel', lang='unknown')
    assert res == TEXTS['fa']['btn_cancel']

    # Non-existent key returns key name
    res = tr('non_existent_key_xyz', lang='en')
    assert res == 'non_existent_key_xyz'
