"""Server-side Google and Kakao OAuth/OIDC login routes (Authlib)."""
from __future__ import annotations

import secrets
from collections.abc import Mapping
from typing import Any

from authlib.integrations.base_client.errors import OAuthError
from flask import Blueprint, current_app, flash, redirect, request, session, url_for
from flask_babel import gettext as _
from requests.exceptions import HTTPError, RequestException

from extensions.oauth import SUPPORTED_PROVIDERS, oauth, provider_configured
from routes import establish_session
from services.auth_service import (
    OAuthEmailMissing,
    OAuthEmailUnverified,
    OAuthLoginError,
    build_claims,
    resolve_oauth_user,
)
from services.redirect_safety import is_safe_local_path, safe_redirect_target

oauth_bp = Blueprint('oauth', __name__)

_NONCE_KEY = 'oauth_nonce'
_NEXT_KEY = 'oauth_next'

KAKAO_OIDC_USERINFO_URL = 'https://kapi.kakao.com/v1/oidc/userinfo'
KAKAO_USER_ME_URL = 'https://kapi.kakao.com/v2/user/me'
KAKAO_EMAIL_PROPERTY_KEYS = '["kakao_account.email"]'
KAKAO_FORM_CONTENT_TYPE = 'application/x-www-form-urlencoded;charset=utf-8'

PROVIDER_LABELS = {'google': 'Google', 'kakao': 'Kakao'}


def _provider_label(provider: str) -> str:
    return PROVIDER_LABELS.get(provider, provider)


def _unsupported(provider: str) -> Any:
    flash(_('That sign-in provider is not available.'), 'danger')
    current_app.logger.warning('Rejected OAuth request for unsupported provider.')
    return redirect(url_for('auth.login'))


@oauth_bp.route('/<provider>')
def login(provider: str) -> Any:
    """Begin the OAuth authorization flow for an allowlisted provider."""
    if provider not in SUPPORTED_PROVIDERS:
        return _unsupported(provider)
    if not provider_configured(provider):
        flash(
            _('%(provider)s sign-in is not configured on this server.',
              provider=_provider_label(provider)),
            'warning',
        )
        return redirect(url_for('auth.login'))

    next_target = request.args.get('next')
    if is_safe_local_path(next_target):
        session[_NEXT_KEY] = next_target
    else:
        session.pop(_NEXT_KEY, None)

    nonce = secrets.token_urlsafe(16)
    session[_NONCE_KEY] = nonce
    client = oauth.create_client(provider)
    redirect_uri = url_for('oauth.callback', provider=provider, _external=True)
    return client.authorize_redirect(redirect_uri, nonce=nonce)


@oauth_bp.route('/<provider>/callback')
def callback(provider: str) -> Any:
    """Validate the OAuth callback and establish an authenticated session."""
    if provider not in SUPPORTED_PROVIDERS:
        return _unsupported(provider)
    if not provider_configured(provider):
        flash(
            _('%(provider)s sign-in is not configured on this server.',
              provider=_provider_label(provider)),
            'warning',
        )
        return redirect(url_for('auth.login'))

    nonce = session.pop(_NONCE_KEY, None)
    next_target = session.pop(_NEXT_KEY, None)
    client = oauth.create_client(provider)

    try:
        # Authlib validates the OAuth state against the session here.
        token = client.authorize_access_token()
        if provider == 'kakao':
            userinfo = _resolve_kakao_userinfo(client, token, nonce)
        else:
            userinfo = _extract_userinfo(client, token, nonce)
    except OAuthError as exc:
        current_app.logger.warning(
            'OAuth callback failed during token exchange (provider=%s, error=%s).',
            provider, exc.error,
        )
        flash(_('Sign-in could not be completed. Please try again.'), 'danger')
        return redirect(url_for('auth.login'))

    try:
        claims = build_claims(provider, userinfo)  # type: ignore[arg-type]
        user = resolve_oauth_user(provider, claims)  # type: ignore[arg-type]
    except OAuthEmailMissing:
        current_app.logger.info('OAuth login rejected: no email returned (provider=%s).', provider)
        flash(
            _('We could not get a verified email from %(provider)s. Please grant '
              'email permission and try again.', provider=_provider_label(provider)),
            'warning',
        )
        return redirect(url_for('auth.login'))
    except OAuthEmailUnverified:
        current_app.logger.info('OAuth login rejected: email not verified (provider=%s).', provider)
        flash(
            _('Your %(provider)s email is not verified, so we cannot link the account.',
              provider=_provider_label(provider)),
            'warning',
        )
        return redirect(url_for('auth.login'))
    except OAuthLoginError:
        current_app.logger.warning('OAuth login failed during account resolution (provider=%s).', provider)
        flash(_('Sign-in could not be completed. Please try again.'), 'danger')
        return redirect(url_for('auth.login'))

    establish_session(user, provider=provider)
    current_app.logger.info(
        'OAuth login succeeded (provider=%s, user_id=%s).', provider, str(user['_id'])
    )
    flash(_('Welcome back, %(username)s!', username=user['username']), 'success')
    return redirect(safe_redirect_target(next_target))


def _plain_token(token: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize an Authlib token mapping to a plain dict."""
    return dict(token)


def _api_token(token: Mapping[str, Any]) -> dict[str, str] | None:
    """Return a bearer-only token payload for Kakao API calls."""
    plain = _plain_token(token)
    access_token = str(plain.get('access_token') or '').strip()
    if not access_token:
        return None
    token_type = str(plain.get('token_type') or 'bearer').strip() or 'bearer'
    return {'access_token': access_token, 'token_type': token_type}


def _log_kakao_api_failure(endpoint: str, exc: RequestException) -> None:
    """Log Kakao API failures with HTTP status and error payload when present."""
    status = getattr(getattr(exc, 'response', None), 'status_code', None)
    body: Any = None
    response = getattr(exc, 'response', None)
    if response is not None:
        try:
            body = response.json()
        except ValueError:
            body = (response.text or '')[:200]
    current_app.logger.warning(
        'Kakao %s lookup failed (status=%s, body=%s).',
        endpoint,
        status,
        body,
    )


def _id_token_claims(
    client: Any,
    token: Mapping[str, Any],
    nonce: str | None,
) -> dict[str, Any]:
    """Return validated ID-token claims when available."""
    plain = _plain_token(token)
    userinfo = plain.get('userinfo')
    if userinfo:
        return dict(userinfo)
    if nonce is not None:
        parsed = client.parse_id_token(plain, nonce=nonce)
        if parsed:
            return dict(parsed)
    return {}


def _fetch_kakao_oidc_userinfo(client: Any, api_token: Mapping[str, str]) -> dict[str, Any] | None:
    """Fetch OIDC userinfo (``email_verified``) per Kakao OIDC docs."""
    try:
        resp = client.get(KAKAO_OIDC_USERINFO_URL, token=api_token)
        resp.raise_for_status()
        return resp.json()
    except RequestException as exc:
        _log_kakao_api_failure('oidc/userinfo', exc)
        return None


def _fetch_kakao_account_email(client: Any, api_token: Mapping[str, str]) -> dict[str, Any] | None:
    """Fetch email verification flags via Kakao's documented user/me request."""
    try:
        resp = client.post(
            KAKAO_USER_ME_URL,
            token=api_token,
            headers={'Content-Type': KAKAO_FORM_CONTENT_TYPE},
            data={'property_keys': KAKAO_EMAIL_PROPERTY_KEYS},
        )
        resp.raise_for_status()
        account = resp.json().get('kakao_account')
        return dict(account) if isinstance(account, Mapping) else None
    except RequestException as exc:
        _log_kakao_api_failure('v2/user/me', exc)
        return None


def _resolve_kakao_userinfo(
    client: Any,
    token: Mapping[str, Any],
    nonce: str | None,
) -> dict[str, Any]:
    """Resolve Kakao login claims with verified email per official Kakao APIs.

    Kakao's ID token may include ``email`` but omits ``email_verified``. Kakao
    documents that verification must be read from either:

    * OIDC userinfo ``email_verified``, or
    * REST user/me ``kakao_account.is_email_valid`` + ``is_email_verified``.
    """
    claims = _id_token_claims(client, token, nonce)
    api_token = _api_token(token)
    if api_token is None:
        return claims

    oidc = _fetch_kakao_oidc_userinfo(client, api_token)
    if oidc:
        claims.update({key: value for key, value in oidc.items() if value is not None})

    if claims.get('email_verified') is True:
        return claims

    account = _fetch_kakao_account_email(client, api_token)
    if account:
        if email := account.get('email'):
            claims['email'] = email
        if account.get('is_email_valid') and account.get('is_email_verified'):
            claims['email_verified'] = True
        profile = account.get('profile') or {}
        if nickname := profile.get('nickname'):
            claims.setdefault('nickname', nickname)

    return claims


def _extract_userinfo(client: Any, token: Mapping[str, Any], nonce: str | None) -> Mapping[str, Any]:
    """Return OIDC claims, preferring the userinfo endpoint over ID-token claims."""
    try:
        userinfo = client.userinfo(token=token)
        if userinfo:
            return dict(userinfo)
    except (OAuthError, HTTPError, RequestException):
        current_app.logger.info('OIDC userinfo unavailable; falling back to ID token claims.')

    return _id_token_claims(client, token, nonce)
