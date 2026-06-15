"""OAuth identity repository (MongoDB ``oauth_identities`` collection).

A provider identity links an external ``(provider, subject)`` pair to a local
user. Provider tokens are intentionally never stored — the application only
needs authentication, not long-term API access.
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, Literal

from bson import ObjectId

from extensions.db import mongo

Provider = Literal['google', 'kakao']


def _now() -> datetime:
    return datetime.now(UTC)


def find_identity(provider: str, subject: str) -> Mapping[str, Any] | None:
    """Look up an identity by its provider + subject pair."""
    return mongo.db.oauth_identities.find_one({'provider': provider, 'subject': subject})


def create_identity(
    user_id: ObjectId,
    provider: Provider,
    subject: str,
    *,
    provider_email: str | None,
    email_verified: bool,
    display_name: str | None = None,
    avatar_url: str | None = None,
) -> str:
    """Insert a new provider identity and return its id.

    Raises ``pymongo.errors.DuplicateKeyError`` if the ``(provider, subject)``
    pair already exists; callers handle that as a concurrent-creation race.
    """
    now = _now()
    doc: dict[str, Any] = {
        'user_id': user_id,
        'provider': provider,
        'subject': subject,
        'provider_email': provider_email,
        'email_verified': email_verified,
        'display_name': display_name,
        'avatar_url': avatar_url,
        'created_at': now,
        'updated_at': now,
    }
    result = mongo.db.oauth_identities.insert_one(doc)
    return str(result.inserted_id)


def touch_identity(
    provider: str,
    subject: str,
    *,
    provider_email: str | None,
    avatar_url: str | None = None,
    display_name: str | None = None,
) -> None:
    """Refresh identity metadata on login (email, avatar, display name)."""
    updates: dict[str, Any] = {'updated_at': _now(), 'provider_email': provider_email}
    if avatar_url:
        updates['avatar_url'] = avatar_url
    if display_name:
        updates['display_name'] = display_name
    mongo.db.oauth_identities.update_one(
        {'provider': provider, 'subject': subject},
        {'$set': updates},
    )


def find_avatar_for_user(user_id: str | ObjectId) -> str | None:
    """Return the newest OAuth provider avatar URL for a user, if any."""
    doc = mongo.db.oauth_identities.find_one(
        {
            'user_id': ObjectId(user_id),
            'avatar_url': {'$type': 'string', '$ne': ''},
        },
        sort=[('updated_at', -1)],
        projection={'avatar_url': 1},
    )
    if not doc:
        return None
    url = doc.get('avatar_url')
    return url if isinstance(url, str) and url.strip() else None
