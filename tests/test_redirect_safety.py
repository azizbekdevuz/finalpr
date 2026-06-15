"""Open-redirect protection tests."""
from __future__ import annotations

from services.redirect_safety import is_safe_local_path, safe_redirect_target


def test_local_paths_are_safe(app):
    with app.test_request_context('/'):
        assert is_safe_local_path('/spots') is True
        assert is_safe_local_path('/reviews?page=2') is True


def test_empty_target_is_unsafe(app):
    with app.test_request_context('/'):
        assert is_safe_local_path('') is False
        assert is_safe_local_path(None) is False


def test_scheme_relative_url_is_rejected(app):
    with app.test_request_context('/'):
        assert is_safe_local_path('//evil.example/path') is False


def test_absolute_external_url_is_rejected(app):
    with app.test_request_context('/'):
        assert is_safe_local_path('https://evil.example/phish') is False


def test_safe_redirect_target_falls_back(app):
    with app.test_request_context('/'):
        assert safe_redirect_target('https://evil.example') == '/'
        assert safe_redirect_target('/spots') == '/spots'
