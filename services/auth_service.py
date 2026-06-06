"""Account resolution, linking and normalization for OAuth/OIDC logins.

This module owns session-independent business logic only. The Flask layer is
responsible for establishing the session after :func:`resolve_oauth_user`
returns a user document.
"""
from __future__ import annotations

import re
import secrets
from collections.abc import Mapping
from typing import Any, TypedDict

from pymongo.errors import DuplicateKeyError

import models.oauth_identity as IdentityModel
import models.user as UserModel
from models.oauth_identity import Provider

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
_USERNAME_SAFE_RE = re.compile(r'[^a-z0-9_]+')


class OAuthLoginError(Exception):
    """Base class for recoverable OAuth login failures."""

    #: Stable code the route maps to a translated, user-facing message.
    code = 'oauth_failed'


class OAuthEmailMissing(OAuthLoginError):
    code = 'email_missing'


class OAuthEmailUnverified(OAuthLoginError):
    code = 'email_unverified'


class OAuthClaims(TypedDict):
    subject: str
    email: str
    email_normalized: str
    email_verified: bool
    display_name: str | None
    avatar_url: str | None


def normalize_email(raw: str | None) -> str:
    """Normalize an email: trim + lowercase. Raises ``ValueError`` if invalid.

    The local part is not altered beyond case folding (no Gmail dot/plus
    stripping), to avoid silently merging distinct addresses.
    """
    candidate = (raw or '').strip()
    if not candidate or not _EMAIL_RE.match(candidate):
        raise ValueError('invalid email address')
    return candidate.lower()


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {'true', '1', 'yes'}
    return False


def build_claims(provider: Provider, userinfo: Mapping[str, Any]) -> OAuthClaims:
    """Map an Authlib-validated ``userinfo`` mapping into normalized claims.

    Uses standard OpenID Connect claim names. ``email_normalized`` is empty when
    the provider did not return a usable email (e.g. missing consent).
    """
    subject = str(userinfo.get('sub', '')).strip()
    raw_email = userinfo.get('email')
    display_name = userinfo.get('name') or userinfo.get('nickname')
    avatar_url = userinfo.get('picture')

    try:
        email_normalized = normalize_email(raw_email)
    except ValueError:
        email_normalized = ''

    return OAuthClaims(
        subject=subject,
        email=(raw_email or '').strip(),
        email_normalized=email_normalized,
        email_verified=_as_bool(userinfo.get('email_verified')),
        display_name=display_name.strip() if isinstance(display_name, str) else None,
        avatar_url=avatar_url if isinstance(avatar_url, str) else None,
    )


def _sanitize_username(raw: str | None) -> str:
    """Build a valid username candidate from arbitrary provider text."""
    base = (raw or '').strip().lower()
    base = base.split('@', 1)[0]
    base = _USERNAME_SAFE_RE.sub('_', base).strip('_')
    if len(base) < 3:
        base = f'user_{secrets.token_hex(3)}'
    return base[:24]


def generate_unique_username(seed: str | None) -> str:
    """Return a username not currently present, derived from ``seed``."""
    base = _sanitize_username(seed)
    if not UserModel.username_exists(base):
        return base
    for _ in range(8):
        candidate = f'{base[:18]}_{secrets.token_hex(2)}'
        if not UserModel.username_exists(candidate):
            return candidate
    return f'user_{secrets.token_hex(5)}'


def _link_existing_user(
    provider: Provider,
    subject: str,
    user: Mapping[str, Any],
    claims: OAuthClaims,
    *,
    stale_identity: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    """Attach a provider identity to an existing user (idempotent)."""
    user_id = user['_id']
    if stale_identity is not None:
        # Re-point orphaned identity after user deletion. / 삭제된 사용자에 묶인 identity를 재연결합니다.
        from extensions.db import mongo
        mongo.db.oauth_identities.update_one(
            {'_id': stale_identity['_id']},
            {'$set': {'user_id': user_id, 'provider_email': claims['email_normalized']}},
        )
    else:
        try:
            IdentityModel.create_identity(
                user_id, provider, subject,
                provider_email=claims['email_normalized'],
                email_verified=claims['email_verified'],
                display_name=claims['display_name'],
                avatar_url=claims['avatar_url'],
            )
        except DuplicateKeyError:
            # Concurrent callback won the race; reuse its identity. / 동시 콜백이 먼저 생성한 identity를 재사용합니다.
            existing = IdentityModel.find_identity(provider, subject)
            if existing:
                linked = UserModel.find_by_id(existing['user_id'])
                if linked:
                    return linked
    UserModel.fill_missing_profile(user, {'email_normalized': claims['email_normalized']})
    return user


def resolve_oauth_user(provider: Provider, claims: OAuthClaims) -> Mapping[str, Any]:
    """Resolve (or create) the local user for an OAuth login.

    Raises :class:`OAuthEmailMissing` / :class:`OAuthEmailUnverified` when an
    account cannot be safely created or linked.
    """
    subject = claims['subject']
    if not subject:
        raise OAuthLoginError('missing subject')

    identity = IdentityModel.find_identity(provider, subject)
    if identity:
        user = UserModel.find_by_id(identity['user_id'])
        if user:
            IdentityModel.touch_identity(
                provider, subject, provider_email=claims['email_normalized']
            )
            return user
        # Orphan identity: rebuild link below. / 고아 identity는 아래에서 다시 연결합니다.

    if not claims['email_normalized']:
        raise OAuthEmailMissing()
    if not claims['email_verified']:
        raise OAuthEmailUnverified()

    existing = UserModel.find_by_normalized_email(claims['email_normalized'])
    if existing:
        return _link_existing_user(
            provider, subject, existing, claims, stale_identity=identity
        )

    return _create_oauth_user(provider, subject, claims, stale_identity=identity)


def _create_oauth_user(
    provider: Provider,
    subject: str,
    claims: OAuthClaims,
    *,
    stale_identity: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    """Create a fresh OAuth user, handling username/email races safely."""
    seed = claims['display_name'] or claims['email_normalized']
    for _ in range(6):
        username = generate_unique_username(seed)
        try:
            user_id = UserModel.create_oauth_user(
                username, claims['email'], email_normalized=claims['email_normalized']
            )
        except DuplicateKeyError:
            # Username/email race: link if email already exists. / 동시 삽입 충돌 시 기존 이메일 계정에 연결합니다.
            by_email = UserModel.find_by_normalized_email(claims['email_normalized'])
            if by_email:
                return _link_existing_user(
                    provider, subject, by_email, claims, stale_identity=stale_identity
                )
            continue
        user = UserModel.find_by_id(user_id)
        assert user is not None
        return _link_existing_user(
            provider, subject, user, claims, stale_identity=stale_identity
        )
    raise OAuthLoginError('could not allocate username')
