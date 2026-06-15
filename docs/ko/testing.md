# 테스트·검증

<p align="right">
  <strong>한국어</strong> ·
  <a href="../en/testing.md">English</a>
</p>

개발 의존성 설치:

```bash
pip install -r requirements-dev.txt
```

## 명령

```bash
ruff check .
mypy app.py config.py extensions routes models services
pytest -q
```

## 범위

`tests/`에는 인증, OAuth 라우트, i18n, 리다이렉트 안전성, 템플릿 렌더링 등이 포함됩니다. MongoDB는 테스트에서 `mongomock`을 사용합니다.

## CI 권장

PR 전에 위 세 명령을 모두 통과시키세요. OAuth·Kakao 관련 변경 시 `tests/test_oauth_routes.py`를 반드시 확인하세요.
