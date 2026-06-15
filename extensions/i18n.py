"""Flask-Babel wiring and locale selection for Korean/English localization."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from babel.dates import format_datetime as babel_format_datetime
from flask import current_app, request, session
from flask_babel import Babel, get_locale

if TYPE_CHECKING:  # pragma: no cover - typing only
    from flask import Flask

babel = Babel()

SESSION_LOCALE_KEY = 'locale'

#: Human-readable names shown in the language switcher.
LANGUAGE_NAMES: dict[str, str] = {
    'ko': '한국어',
    'en': 'English',
}


def supported_locales() -> tuple[str, ...]:
    """Supported locale codes from configuration (falls back to ko/en)."""
    return tuple(current_app.config.get('SUPPORTED_LOCALES', ('ko', 'en')))


def is_supported(locale: str | None) -> bool:
    """Return ``True`` when ``locale`` is an allowed code."""
    return bool(locale) and locale in supported_locales()


def select_locale() -> str:
    """Resolve the active locale.

    Order: session value -> best ``Accept-Language`` match -> default locale.
    Only allowlisted codes are ever returned.
    """
    stored = session.get(SESSION_LOCALE_KEY)
    if is_supported(stored):
        return stored  # type: ignore[return-value]

    best = request.accept_languages.best_match(list(supported_locales()))
    if is_supported(best):
        return best  # type: ignore[return-value]

    return current_app.config.get('BABEL_DEFAULT_LOCALE', 'ko')


def init_i18n(app: Flask) -> None:
    """Initialise Babel with the locale selector (Flask-Babel 4 style)."""
    babel.init_app(app, locale_selector=select_locale)

    @app.template_filter('display_datetime')
    def display_datetime_filter(value: datetime | None) -> str:
        """Locale-aware datetime safe on Windows (avoids non-ASCII strftime format strings)."""
        if value is None:
            return ''
        locale = str(get_locale() or app.config.get('BABEL_DEFAULT_LOCALE', 'ko'))
        if locale.startswith('en'):
            return babel_format_datetime(value, 'MMM d, yyyy HH:mm', locale='en')
        return (
            f'{value.year}년 {value.month:02d}월 {value.day:02d}일 '
            f'{value.hour:02d}:{value.minute:02d}'
        )
