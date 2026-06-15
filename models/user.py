"""User repository (MongoDB ``users`` collection).

Supports both the legacy credential accounts (username + password hash) and new
OAuth-capable accounts that may not carry a password. A normalized email field
(``email_normalized``) is written for new/updated records, while lookups stay
compatible with legacy documents that predate that field.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from werkzeug.security import check_password_hash, generate_password_hash

from extensions.db import mongo


def _now() -> datetime:
    return datetime.now(UTC)


def create_user(username: str, email: str, password: str, role: str = 'user') -> str:
    """Create a credential user (username + password) and return its id."""
    user: dict[str, Any] = {
        'username': username,
        'email': email,
        'email_normalized': normalize_email_field(email),
        'password_hash': generate_password_hash(password),
        'role': role,
        'created_at': _now(),
    }
    result = mongo.db.users.insert_one(user)
    return str(result.inserted_id)


def create_oauth_user(
    username: str,
    email: str,
    role: str = 'user',
    *,
    email_normalized: str | None = None,
) -> str:
    """Create an OAuth-only user (no password hash) and return its id."""
    user: dict[str, Any] = {
        'username': username,
        'email': email,
        'email_normalized': email_normalized or normalize_email_field(email),
        'role': role,
        'created_at': _now(),
    }
    result = mongo.db.users.insert_one(user)
    return str(result.inserted_id)


def normalize_email_field(email: str | None) -> str:
    """Best-effort normalization used for stored ``email_normalized`` values."""
    return (email or '').strip().lower()


def find_by_username(username: str) -> Mapping[str, Any] | None:
    return mongo.db.users.find_one({'username': username})


def find_by_email(email: str) -> Mapping[str, Any] | None:
    return mongo.db.users.find_one({'email': email})


def find_by_normalized_email(normalized: str) -> Mapping[str, Any] | None:
    """Find a user by normalized email, tolerant of legacy mixed-case records."""
    if not normalized:
        return None
    pattern = f'^{re.escape(normalized)}$'
    return mongo.db.users.find_one({
        '$or': [
            {'email_normalized': normalized},
            {'email': {'$regex': pattern, '$options': 'i'}},
        ]
    })


def find_by_id(user_id: str | ObjectId) -> Mapping[str, Any] | None:
    return mongo.db.users.find_one({'_id': ObjectId(user_id)})


def verify_password(user_doc: Mapping[str, Any], password: str) -> bool:
    """Verify a password; returns ``False`` safely for OAuth-only users."""
    stored = user_doc.get('password_hash')
    if not stored:
        return False
    return check_password_hash(stored, password)


def username_exists(username: str) -> bool:
    return mongo.db.users.find_one({'username': username}) is not None


def email_exists(email: str) -> bool:
    """True when the email already exists (checks normalized + legacy values)."""
    return find_by_normalized_email(normalize_email_field(email)) is not None


#: Fields that must never be overwritten by OAuth profile linking.
_PROTECTED_FIELDS = frozenset({'username', 'role', 'password_hash', '_id', 'email'})


def fill_missing_profile(user_doc: Mapping[str, Any], candidates: Mapping[str, Any]) -> None:
    """Set candidate profile fields only when currently missing/empty.

    Protected identity fields are ignored so an existing username, role or
    password hash can never be clobbered during account linking.
    """
    updates = {
        key: value
        for key, value in candidates.items()
        if value and key not in _PROTECTED_FIELDS and not user_doc.get(key)
    }
    if not updates:
        return
    mongo.db.users.update_one({'_id': user_doc['_id']}, {'$set': updates})
