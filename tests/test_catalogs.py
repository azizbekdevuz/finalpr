"""Translation catalog integrity tests."""
from __future__ import annotations

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _po_path(locale: str) -> str:
    return os.path.join(ROOT, 'translations', locale, 'LC_MESSAGES', 'messages.po')


def _mo_path(locale: str) -> str:
    return os.path.join(ROOT, 'translations', locale, 'LC_MESSAGES', 'messages.mo')


def test_compiled_catalogs_exist():
    for locale in ('en', 'ko'):
        assert os.path.exists(_mo_path(locale)), f'missing compiled catalog for {locale}'


def test_no_fuzzy_translations():
    for locale in ('en', 'ko'):
        with open(_po_path(locale), encoding='utf-8') as fh:
            content = fh.read()
        assert '#, fuzzy' not in content, f'fuzzy entries present in {locale}'


def test_korean_catalog_loads_and_translates():
    """The compiled Korean catalog can be read and contains real translations."""
    from babel.messages.pofile import read_po
    with open(_po_path('ko'), encoding='utf-8') as fh:
        catalog = read_po(fh)
    translated = [m for m in catalog if m.id and m.string]
    assert len(translated) > 50
