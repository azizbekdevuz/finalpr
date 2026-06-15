# Testing

<p align="right">
  <a href="../ko/testing.md">한국어</a> ·
  <strong>English</strong>
</p>

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

## Commands

```bash
ruff check .
mypy app.py config.py extensions routes models services
pytest -q
```

## Coverage

`tests/` includes auth, OAuth routes, i18n, redirect safety, and template rendering. Tests use `mongomock` instead of a live MongoDB instance.

## CI recommendation

Run all three commands before opening a PR. For OAuth or Kakao changes, review `tests/test_oauth_routes.py`.
