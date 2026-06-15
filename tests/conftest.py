"""Shared pytest fixtures.

The whole suite runs against an in-memory ``mongomock`` database and never
touches a real MongoDB, Ollama, TourAPI or OAuth provider. Flask-PyMongo's
``init_app`` is monkeypatched so the application factory wires up the mock
client transparently.
"""
from __future__ import annotations

import mongomock
import pytest
from flask_pymongo import PyMongo

from config import Config


class TestConfig(Config):
    TESTING = True
    DEBUG = True
    SECRET_KEY = 'test-secret-key'
    SERVER_NAME = 'localhost'
    WTF_CSRF_ENABLED = False
    # Configure both providers so provider_configured() is True in tests.
    GOOGLE_CLIENT_ID = 'test-google-id'
    GOOGLE_CLIENT_SECRET = 'test-google-secret'
    KAKAO_CLIENT_ID = 'test-kakao-id'
    KAKAO_CLIENT_SECRET = 'test-kakao-secret'


class TestConfigNoOAuth(Config):
    TESTING = True
    DEBUG = True
    SECRET_KEY = 'test-secret-key'
    SERVER_NAME = 'localhost'
    GOOGLE_CLIENT_ID = ''
    GOOGLE_CLIENT_SECRET = ''
    KAKAO_CLIENT_ID = ''
    KAKAO_CLIENT_SECRET = ''


def _reset_oauth() -> None:
    """Clear the module-global Authlib registry between app builds."""
    from extensions.oauth import oauth
    oauth._registry = {}
    oauth._clients = {}


def _build_app(monkeypatch, config_object):
    client = mongomock.MongoClient()

    def fake_init_app(self, app, *args, **kwargs):
        self.cx = client
        self.db = client['test_tourism']

    monkeypatch.setattr(PyMongo, 'init_app', fake_init_app)
    _reset_oauth()

    from app import create_app
    return create_app(config_object)


@pytest.fixture
def app(monkeypatch):
    yield _build_app(monkeypatch, TestConfig)


@pytest.fixture
def app_no_oauth(monkeypatch):
    yield _build_app(monkeypatch, TestConfigNoOAuth)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    from extensions.db import mongo
    return mongo.db
