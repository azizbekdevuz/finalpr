"""Smoke tests: core pages render offline for both locales."""
from __future__ import annotations

import pytest

import models.user as UserModel
from extensions.i18n import SESSION_LOCALE_KEY

PUBLIC_PAGES = ['/', '/auth/login', '/auth/register', '/spots/?sort=popular',
                '/reviews/', '/courses/']


@pytest.mark.parametrize('path', PUBLIC_PAGES)
def test_public_pages_render_korean(client, db, path):
    assert client.get(path).status_code == 200


@pytest.mark.parametrize('path', PUBLIC_PAGES)
def test_public_pages_render_english(client, db, path):
    with client.session_transaction() as sess:
        sess[SESSION_LOCALE_KEY] = 'en'
    assert client.get(path).status_code == 200


def test_dashboard_requires_login(client, db):
    resp = client.get('/dashboard')
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers['Location']


def test_admin_db_requires_admin(client, db):
    resp = client.get('/admin/db')
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers['Location']


def test_admin_db_blocks_non_admin_user(client, db):
    UserModel.create_user('plain', 'plain@example.com', 'pw123456', role='user')
    client.post('/auth/login', data={'username': 'plain', 'password': 'pw123456'})
    resp = client.get('/admin/db')
    assert resp.status_code in (302, 403)


def test_all_templates_compile(app):
    """Every template loads through the Jinja environment without syntax errors."""
    env = app.jinja_env
    names = env.list_templates(filter_func=lambda n: n.endswith('.html'))
    assert names
    for name in names:
        env.get_template(name)


def test_base_includes_liquid_background(client, db):
    resp = client.get('/')
    html = resp.get_data(as_text=True)
    assert 'liquid-bg' in html
    assert 'liquid-bg.js' in html
    assert 'liquid-bg__canvas' in html
