"""Localization and language-switching tests."""
from __future__ import annotations

from extensions.i18n import SESSION_LOCALE_KEY


def test_default_locale_renders_korean(client, db):
    resp = client.get('/')
    body = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert 'lang="ko"' in body
    assert '가보자고' in body


def test_english_session_renders_english(client, db):
    with client.session_transaction() as sess:
        sess[SESSION_LOCALE_KEY] = 'en'
    body = client.get('/').get_data(as_text=True)
    assert 'lang="en"' in body
    assert 'Gabojago' in body


def test_korean_session_renders_korean(client, db):
    with client.session_transaction() as sess:
        sess[SESSION_LOCALE_KEY] = 'ko'
    body = client.get('/').get_data(as_text=True)
    assert '여행 후기' in body


def test_unsupported_locale_is_rejected(client, db):
    client.post('/language/zz', data={'next': '/'})
    with client.session_transaction() as sess:
        assert sess.get(SESSION_LOCALE_KEY) != 'zz'


def test_language_switch_redirects_locally(client, db):
    resp = client.post('/language/en', data={'next': 'https://evil.example'})
    assert resp.status_code == 302
    assert 'evil.example' not in resp.headers['Location']


def test_language_switch_persists_in_session(client, db):
    client.post('/language/en', data={'next': '/'})
    with client.session_transaction() as sess:
        assert sess[SESSION_LOCALE_KEY] == 'en'


def test_locale_persists_through_logout(client, db):
    client.post('/language/en', data={'next': '/'})
    client.get('/auth/logout')
    with client.session_transaction() as sess:
        assert sess[SESSION_LOCALE_KEY] == 'en'


def test_flash_uses_selected_locale_english(client, db):
    with client.session_transaction() as sess:
        sess[SESSION_LOCALE_KEY] = 'en'
    resp = client.post('/auth/login', data={'username': 'nope', 'password': 'bad'})
    assert 'Incorrect username or password.' in resp.get_data(as_text=True)


def test_flash_uses_selected_locale_korean(client, db):
    with client.session_transaction() as sess:
        sess[SESSION_LOCALE_KEY] = 'ko'
    resp = client.post('/auth/login', data={'username': 'nope', 'password': 'bad'})
    assert '아이디 또는 비밀번호가 올바르지 않습니다.' in resp.get_data(as_text=True)
