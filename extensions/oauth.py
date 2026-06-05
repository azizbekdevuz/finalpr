"""Authlib OAuth client wiring for Google and Kakao (OpenID Connect).

The :class:`~authlib.integrations.flask_client.OAuth` instance is created once
and initialised inside the application factory. Providers are registered only
when their credentials are present, so the application still boots cleanly in
local development without OAuth secrets configured.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from authlib.integrations.flask_client import OAuth

if TYPE_CHECKING:  # pragma: no cover - typing only
    from flask import Flask

oauth = OAuth()

GOOGLE_METADATA_URL = 'https://accounts.google.com/.well-known/openid-configuration'
KAKAO_METADATA_URL = 'https://kauth.kakao.com/.well-known/openid-configuration'

#: Providers the application is allowed to talk to (strict allowlist).
SUPPORTED_PROVIDERS: tuple[str, ...] = ('google', 'kakao')


def init_oauth(app: Flask) -> None:
    """Initialise the OAuth client and register configured providers."""
    oauth.init_app(app)

    if app.config.get('GOOGLE_CLIENT_ID') and app.config.get('GOOGLE_CLIENT_SECRET'):
        oauth.register(
            name='google',
            client_id=app.config['GOOGLE_CLIENT_ID'],
            client_secret=app.config['GOOGLE_CLIENT_SECRET'],
            server_metadata_url=GOOGLE_METADATA_URL,
            client_kwargs={'scope': 'openid profile email'},
        )

    if app.config.get('KAKAO_CLIENT_ID'):
        # Kakao uses the REST API key as the OAuth client id. The client secret
        # is optional and only sent when the Kakao application enables it.
        oauth.register(
            name='kakao',
            client_id=app.config['KAKAO_CLIENT_ID'],
            client_secret=app.config.get('KAKAO_CLIENT_SECRET') or None,
            server_metadata_url=KAKAO_METADATA_URL,
            # Kakao REST APIs (user/me, OIDC userinfo) live on kapi.kakao.com.
            api_base_url='https://kapi.kakao.com',
            userinfo_endpoint='https://kapi.kakao.com/v1/oidc/userinfo',
            client_kwargs={
                'scope': 'openid profile_nickname profile_image account_email',
                'token_endpoint_auth_method': 'client_secret_post',
            },
        )


def provider_configured(name: str) -> bool:
    """Return ``True`` when ``name`` is a registered, usable provider."""
    if name not in SUPPORTED_PROVIDERS:
        return False
    return getattr(oauth, name, None) is not None
