"""Server-side language switching."""
from __future__ import annotations

from typing import Any

from flask import Blueprint, flash, redirect, request, session
from flask_babel import gettext as _
from flask_babel import refresh

from extensions.i18n import SESSION_LOCALE_KEY, is_supported
from services.redirect_safety import safe_redirect_target

language_bp = Blueprint('language', __name__)


@language_bp.route('/<locale>', methods=['POST'])
def set_language(locale: str) -> Any:
    """Persist a supported locale in the session and re-render locally."""
    target = request.form.get('next') or request.referrer
    if is_supported(locale):
        session[SESSION_LOCALE_KEY] = locale
        # Flash after refresh so message uses new locale. / refresh 후 플래시가 새 locale로 표시됩니다.
        refresh()
        flash(_('Language updated.'), 'success')
    return redirect(safe_redirect_target(target))
