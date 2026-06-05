"""OAuth account-resolution and linking tests (no network)."""
from __future__ import annotations

import pytest
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

import models.oauth_identity as IdentityModel
import models.user as UserModel
from services.auth_service import (
    OAuthEmailMissing,
    OAuthEmailUnverified,
    build_claims,
    normalize_email,
    resolve_oauth_user,
)


def _claims(subject, email='new@example.com', verified=True, name='New User'):
    return build_claims('google', {
        'sub': subject, 'email': email,
        'email_verified': verified, 'name': name,
    })


def test_normalize_email_trims_and_lowercases(app):
    assert normalize_email('  Foo@Example.COM ') == 'foo@example.com'


def test_normalize_email_rejects_invalid(app):
    with pytest.raises(ValueError):
        normalize_email('not-an-email')


def test_existing_identity_logs_into_linked_user(app, db):
    uid = UserModel.create_user('linked', 'linked@example.com', 'pw123456')
    IdentityModel.create_identity(
        ObjectId(uid), 'google', 'sub-1',
        provider_email='linked@example.com', email_verified=True,
    )
    user = resolve_oauth_user('google', _claims('sub-1', 'linked@example.com'))
    assert str(user['_id']) == uid


def test_verified_google_email_links_existing_account(app, db):
    uid = UserModel.create_user('legacy', 'Legacy@Example.com', 'pw123456', role='admin')
    user = resolve_oauth_user('google', _claims('sub-g', 'legacy@example.com'))
    assert str(user['_id']) == uid
    # Role + password hash must be preserved.
    assert user['role'] == 'admin'
    assert db.users.find_one({'_id': ObjectId(uid)})['password_hash']
    assert IdentityModel.find_identity('google', 'sub-g') is not None


def test_verified_kakao_email_links_existing_account(app, db):
    uid = UserModel.create_user('kuser', 'kuser@example.com', 'pw123456')
    claims = build_claims('kakao', {
        'sub': 'k-1', 'email': 'kuser@example.com', 'email_verified': True,
        'nickname': 'Kakao Person',
    })
    user = resolve_oauth_user('kakao', claims)
    assert str(user['_id']) == uid


def test_unverified_email_never_links(app, db):
    UserModel.create_user('target', 'target@example.com', 'pw123456')
    with pytest.raises(OAuthEmailUnverified):
        resolve_oauth_user('google', _claims('sub-x', 'target@example.com', verified=False))


def test_missing_email_fails_safely(app, db):
    with pytest.raises(OAuthEmailMissing):
        resolve_oauth_user('google', _claims('sub-y', email='', verified=True))


def test_new_oauth_user_is_created(app, db):
    user = resolve_oauth_user('google', _claims('sub-new', 'fresh@example.com', name='Fresh'))
    assert user['username']
    assert 'password_hash' not in user
    assert db.users.count_documents({}) == 1


def test_username_collision_is_resolved(app, db):
    UserModel.create_user('fresh', 'taken@example.com', 'pw123456')
    user = resolve_oauth_user('google', _claims('sub-c', 'other@example.com', name='Fresh'))
    assert user['username'] != 'fresh'


def test_provider_subject_uniqueness_enforced(app, db):
    uid = UserModel.create_user('u1', 'u1@example.com', 'pw123456')
    IdentityModel.create_identity(
        ObjectId(uid), 'google', 'dup-sub',
        provider_email='u1@example.com', email_verified=True,
    )
    with pytest.raises(DuplicateKeyError):
        IdentityModel.create_identity(
            ObjectId(uid), 'google', 'dup-sub',
            provider_email='u1@example.com', email_verified=True,
        )


def test_duplicate_callback_is_idempotent(app, db):
    claims = _claims('sub-idem', 'idem@example.com', name='Idem')
    first = resolve_oauth_user('google', claims)
    second = resolve_oauth_user('google', claims)
    assert str(first['_id']) == str(second['_id'])
    assert db.oauth_identities.count_documents({'provider': 'google', 'subject': 'sub-idem'}) == 1


def test_tokens_are_not_persisted(app, db):
    resolve_oauth_user('google', _claims('sub-tok', 'tok@example.com'))
    doc = db.oauth_identities.find_one({'subject': 'sub-tok'})
    assert 'access_token' not in doc
    assert 'token' not in doc
    assert 'id_token' not in doc


def test_kakao_unverified_when_flag_absent(app, db):
    # Kakao userinfo without email_verified must be treated as unverified.
    claims = build_claims('kakao', {'sub': 'k-2', 'email': 'noflag@example.com'})
    assert claims['email_verified'] is False
    with pytest.raises(OAuthEmailUnverified):
        resolve_oauth_user('kakao', claims)
