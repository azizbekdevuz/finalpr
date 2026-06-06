# Localization (i18n)

<p align="right">
  <a href="../ko/localization.md">한국어</a> ·
  <strong>English</strong>
</p>

[Korean (`ko`) and English (`en`) are supported via [Flask-Babel](https://python-babel.github.io/flask-babel/).

## Behavior

- Default locale: `ko`
- Resolution order: session → `Accept-Language` → default
- Navbar switcher or `POST /language/<locale>`

Catalog files: `translations/<locale>/LC_MESSAGES/messages.po`

## After changing strings

```bash
pybabel extract -F babel.cfg -o messages.pot .
pybabel update -i messages.pot -d translations
# edit messages.po
pybabel compile -d translations
```

`babel.cfg` defines extract targets (`templates/`, `routes/`, etc.).

## Templates and code

- Jinja: `{{ _('...') }}`
- Python: `from flask_babel import gettext as _` then `_('...')`
- Run the workflow above when adding new user-visible strings.

## Notes

- Some **content data** (region names, API fields) may remain as stored; application-owned UI copy is translated.
- UI strings such as `REGION_META` resolve in the active request locale.
