"""OAuth callback security tests (Authlib token exchange mocked)."""
from __future__ import annotations

from authlib.integrations.base_client.errors import OAuthError
from requests.exceptions import HTTPError

from extensions.oauth import oauth


def _patch_token(app, monkeypatch, token):
    with app.app_context():
        gclient = oauth.create_client('google')

    def fake_authorize_access_token(self, *args, **kwargs):
        return token

    monkeypatch.setattr(type(gclient), 'authorize_access_token', fake_authorize_access_token)


def _patch_error(app, monkeypatch):
    with app.app_context():
        gclient = oauth.create_client('google')

    def fake_authorize_access_token(self, *args, **kwargs):
        raise OAuthError(error='access_denied')

    monkeypatch.setattr(type(gclient), 'authorize_access_token', fake_authorize_access_token)


def test_state_failure_creates_no_session(client, app, monkeypatch, db):
    _patch_error(app, monkeypatch)
    resp = client.get('/auth/oauth/google/callback')
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers['Location']
    with client.session_transaction() as sess:
        assert 'user_id' not in sess


def test_unsupported_provider_is_rejected(client, db):
    resp = client.get('/auth/oauth/github/callback')
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers['Location']


def test_unconfigured_provider_handled_cleanly(app_no_oauth):
    c = app_no_oauth.test_client()
    resp = c.get('/auth/oauth/google')
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers['Location']


def test_successful_callback_creates_session(client, app, monkeypatch, db):
    token = {'userinfo': {
        'sub': 'g-success', 'email': 'success@example.com',
        'email_verified': True, 'name': 'Success User',
        'picture': 'https://lh3.googleusercontent.com/a/success',
    }}
    _patch_token(app, monkeypatch, token)
    resp = client.get('/auth/oauth/google/callback')
    assert resp.status_code == 302
    with client.session_transaction() as sess:
        assert sess['user_id']
        assert sess['auth_provider'] == 'google'
        assert sess['avatar_url'] == 'https://lh3.googleusercontent.com/a/success'
    assert db.users.count_documents({'email_normalized': 'success@example.com'}) == 1
    # Token material is never persisted.
    ident = db.oauth_identities.find_one({'subject': 'g-success'})
    assert 'access_token' not in ident and 'token' not in ident
    assert ident['avatar_url'] == 'https://lh3.googleusercontent.com/a/success'


def test_callback_unverified_email_rejected(client, app, monkeypatch, db):
    token = {'userinfo': {
        'sub': 'g-unverified', 'email': 'unv@example.com', 'email_verified': False,
    }}
    _patch_token(app, monkeypatch, token)
    resp = client.get('/auth/oauth/google/callback')
    assert resp.status_code == 302
    with client.session_transaction() as sess:
        assert 'user_id' not in sess


def test_callback_missing_email_rejected(client, app, monkeypatch, db):
    token = {'userinfo': {'sub': 'g-noemail', 'name': 'No Email'}}
    _patch_token(app, monkeypatch, token)
    resp = client.get('/auth/oauth/google/callback')
    assert resp.status_code == 302
    with client.session_transaction() as sess:
        assert 'user_id' not in sess


def test_external_next_is_rejected_on_callback(client, app, monkeypatch, db):
    token = {'userinfo': {
        'sub': 'g-next', 'email': 'next@example.com',
        'email_verified': True, 'name': 'Next User',
    }}
    _patch_token(app, monkeypatch, token)
    with client.session_transaction() as sess:
        sess['oauth_next'] = 'https://evil.example/phish'
    resp = client.get('/auth/oauth/google/callback')
    assert resp.status_code == 302
    assert 'evil.example' not in resp.headers['Location']


def test_valid_local_next_is_preserved_on_callback(client, app, monkeypatch, db):
    token = {'userinfo': {
        'sub': 'g-localnext', 'email': 'localnext@example.com',
        'email_verified': True, 'name': 'Local Next',
    }}
    _patch_token(app, monkeypatch, token)
    with client.session_transaction() as sess:
        sess['oauth_next'] = '/spots'
    resp = client.get('/auth/oauth/google/callback')
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/spots')


def _patch_kakao_callback(app, monkeypatch, token, *, userinfo):
    with app.app_context():
        kclient = oauth.create_client('kakao')

    def fake_authorize_access_token(self, *args, **kwargs):
        return token

    class FakeOidcResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return userinfo

    def fake_get(self, url, token=None, **kwargs):
        if 'oidc/userinfo' in url:
            return FakeOidcResponse()
        raise HTTPError('404 Client Error')

    monkeypatch.setattr(type(kclient), 'authorize_access_token', fake_authorize_access_token)
    monkeypatch.setattr(type(kclient), 'get', fake_get)


def test_kakao_uses_userinfo_for_email_verified(client, app, monkeypatch, db):
    """ID-token-style claims without email_verified must not block verified logins."""
    token = {
        'userinfo': {'sub': 'k-verified', 'email': 'kakao@example.com', 'nickname': 'K'},
        'access_token': 'fake',
    }
    _patch_kakao_callback(
        app,
        monkeypatch,
        token,
        userinfo={
            'sub': 'k-verified',
            'email': 'kakao@example.com',
            'email_verified': True,
            'nickname': 'K',
        },
    )
    resp = client.get('/auth/oauth/kakao/callback')
    assert resp.status_code == 302
    with client.session_transaction() as sess:
        assert sess['user_id']
        assert sess['auth_provider'] == 'kakao'
    assert db.users.count_documents({'email_normalized': 'kakao@example.com'}) == 1


def test_extract_userinfo_prefers_oidc_userinfo_endpoint():
    from routes.oauth import _extract_userinfo

    class FakeClient:
        def userinfo(self, token=None, **kwargs):
            return {'sub': 'k-1', 'email': 'u@example.com', 'email_verified': True}

        def parse_id_token(self, token, nonce=None):
            return {'sub': 'k-1', 'email': 'u@example.com'}

    token = {'userinfo': {'sub': 'k-1', 'email': 'u@example.com'}}
    result = _extract_userinfo(FakeClient(), token, 'nonce')
    assert result['email_verified'] is True


def test_resolve_kakao_userinfo_prefers_oidc_email_verified(app):
    from routes.oauth import _resolve_kakao_userinfo

    class FakeClient:
        def get(self, url, token=None, **kwargs):
            class Resp:
                def raise_for_status(self) -> None:
                    return None

                def json(self) -> dict:
                    return {
                        'sub': 'k-1',
                        'email': 'u@example.com',
                        'email_verified': True,
                    }

            return Resp()

        def post(self, url, token=None, **kwargs):
            raise AssertionError('user/me should not be called when OIDC userinfo succeeds')

        def parse_id_token(self, token, nonce=None):
            return {'sub': 'k-1', 'email': 'u@example.com'}

    token = {
        'access_token': 'tok',
        'token_type': 'bearer',
        'userinfo': {'sub': 'k-1', 'email': 'u@example.com'},
    }
    with app.app_context():
        result = _resolve_kakao_userinfo(FakeClient(), token, 'nonce')
    assert result['email_verified'] is True


def test_resolve_kakao_userinfo_falls_back_to_user_me(app):
    from routes.oauth import _resolve_kakao_userinfo

    class FakeClient:
        def get(self, url, token=None, **kwargs):
            raise HTTPError('401 Client Error')

        def post(self, url, token=None, **kwargs):
            class Resp:
                def raise_for_status(self) -> None:
                    return None

                def json(self) -> dict:
                    return {
                        'kakao_account': {
                            'email': 'u@example.com',
                            'is_email_valid': True,
                            'is_email_verified': True,
                        }
                    }

            return Resp()

        def parse_id_token(self, token, nonce=None):
            return {'sub': 'k-1', 'email': 'u@example.com'}

    token = {
        'access_token': 'tok',
        'token_type': 'bearer',
        'userinfo': {'sub': 'k-1', 'email': 'u@example.com'},
    }
    with app.app_context():
        result = _resolve_kakao_userinfo(FakeClient(), token, 'nonce')
    assert result['email_verified'] is True


def test_extract_userinfo_falls_back_on_userinfo_http_error(app):
    from routes.oauth import _extract_userinfo

    class FakeClient:
        def userinfo(self, token=None, **kwargs):
            raise HTTPError('401 Client Error')

        def parse_id_token(self, token, nonce=None):
            return {'sub': 'k-1', 'email': 'u@example.com', 'email_verified': True}

    token = {'id_token': 'jwt'}
    with app.app_context():
        result = _extract_userinfo(FakeClient(), token, 'nonce')
    assert result['email_verified'] is True


def test_kakao_enriches_from_user_me_when_userinfo_fails(client, app, monkeypatch, db):
    with app.app_context():
        kclient = oauth.create_client('kakao')

    token = {
        'access_token': 'fake-access',
        'token_type': 'bearer',
        'userinfo': {'sub': 'k-enrich', 'email': 'kakao@example.com', 'nickname': 'K'},
    }

    def fake_authorize_access_token(self, *args, **kwargs):
        return token

    def fake_get(self, url, token=None, **kwargs):
        raise HTTPError('401 Client Error')

    class FakeMeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                'kakao_account': {
                    'email': 'kakao@example.com',
                    'is_email_valid': True,
                    'is_email_verified': True,
                }
            }

    def fake_post(self, url, token=None, **kwargs):
        return FakeMeResponse()

    monkeypatch.setattr(type(kclient), 'authorize_access_token', fake_authorize_access_token)
    monkeypatch.setattr(type(kclient), 'get', fake_get)
    monkeypatch.setattr(type(kclient), 'post', fake_post)

    resp = client.get('/auth/oauth/kakao/callback')
    assert resp.status_code == 302
    with client.session_transaction() as sess:
        assert sess['user_id']
        assert sess['auth_provider'] == 'kakao'
