"""Shared route helpers: auth decorators and session management."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from functools import wraps
from typing import Any, TypeVar

from flask import flash, redirect, session, url_for
from flask_babel import gettext as _

F = TypeVar('F', bound=Callable[..., Any])

#: Session keys related to authentication (cleared on login/logout).
_AUTH_KEYS = ('user_id', 'username', 'role', 'auth_provider')


def login_required(f: F) -> F:
    """Require an authenticated session for the wrapped view."""
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if 'user_id' not in session:
            flash(_('Please sign in to use this service.'), 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function  # type: ignore[return-value]


def admin_required(f: F) -> F:
    """Require an administrator session for the wrapped view."""
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if 'user_id' not in session:
            flash(_('Please sign in to use this service.'), 'warning')
            return redirect(url_for('auth.login'))
        if session.get('role') != 'admin':
            flash(_('Administrators only.'), 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function  # type: ignore[return-value]


def establish_session(user: Mapping[str, Any], provider: str | None = None) -> None:
    """Rotate auth session to mitigate fixation; preserve locale. / 세션 고정 완화를 위해 인증 세션을 교체하고 locale은 유지합니다."""
    locale = session.get('locale')
    session.clear()
    if locale:
        session['locale'] = locale
    session.permanent = True
    session['user_id'] = str(user['_id'])
    session['username'] = user['username']
    session['role'] = user.get('role', 'user')
    if provider:
        session['auth_provider'] = provider


def logout_session() -> None:
    """Clear authentication data while keeping the selected locale."""
    locale = session.get('locale')
    for key in _AUTH_KEYS:
        session.pop(key, None)
    session.clear()
    if locale:
        session['locale'] = locale
