"""Legacy username/password authentication tests."""
from __future__ import annotations

import models.user as UserModel


def _make_user(username='alice', email='alice@example.com', password='secret123', role='user'):
    return UserModel.create_user(username, email, password, role=role)


def test_existing_user_can_log_in(client, db):
    _make_user()
    resp = client.post('/auth/login', data={'username': 'alice', 'password': 'secret123'})
    assert resp.status_code == 302
    with client.session_transaction() as sess:
        assert sess['user_id']
        assert sess['username'] == 'alice'
        assert sess['role'] == 'user'
        assert sess['auth_provider'] == 'local'


def test_invalid_password_fails(client, db):
    _make_user()
    client.post('/auth/login', data={'username': 'alice', 'password': 'wrong'})
    with client.session_transaction() as sess:
        assert 'user_id' not in sess


def test_oauth_only_user_does_not_crash_credential_login(client, db):
    # OAuth-only user has no password_hash.
    UserModel.create_oauth_user('bob', 'bob@example.com')
    resp = client.post('/auth/login', data={'username': 'bob', 'password': 'anything'})
    assert resp.status_code == 200  # re-renders with error, no crash
    with client.session_transaction() as sess:
        assert 'user_id' not in sess


def test_verify_password_safe_without_hash(app):
    user = {'username': 'bob'}
    assert UserModel.verify_password(user, 'whatever') is False


def test_registration_creates_user(client, db):
    resp = client.post('/auth/register', data={
        'username': 'carol', 'email': 'carol@example.com',
        'password': 'secret123', 'confirm_password': 'secret123',
    })
    assert resp.status_code == 302
    assert UserModel.find_by_username('carol') is not None


def test_duplicate_username_is_rejected(client, db):
    _make_user(username='dave', email='dave@example.com')
    resp = client.post('/auth/register', data={
        'username': 'dave', 'email': 'other@example.com',
        'password': 'secret123', 'confirm_password': 'secret123',
    })
    assert resp.status_code == 200  # validation error re-renders
    assert db.users.count_documents({'username': 'dave'}) == 1


def test_logout_clears_auth(client, db):
    _make_user()
    client.post('/auth/login', data={'username': 'alice', 'password': 'secret123'})
    client.get('/auth/logout')
    with client.session_transaction() as sess:
        assert 'user_id' not in sess
