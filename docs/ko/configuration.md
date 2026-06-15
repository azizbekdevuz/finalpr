# 환경 변수

<p align="right">
  <strong>한국어</strong> ·
  <a href="../en/configuration.md">English</a>
</p>

`.env.example`을 `.env`로 복사한 뒤 실제 값을 채웁니다. **비밀 값은 커밋하지 마세요.**

## 변수 목록

| 변수 | 용도 |
| --- | --- |
| `SECRET_KEY` | Flask 세션 서명 키. 프로덕션 필수. |
| `DEBUG` | `True`/`False`. 프로덕션에서는 `False`. |
| `MONGO_URI` | MongoDB 연결 문자열 |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Google OAuth |
| `KAKAO_CLIENT_ID` / `KAKAO_CLIENT_SECRET` | Kakao REST API 키(및 선택적 시크릿) |
| `SESSION_COOKIE_SECURE` | HTTPS 프로덕션에서 `True`, 로컬 HTTP는 `False` |
| `PREFERRED_URL_SCHEME` | 프로덕션에서 `https` 권장 |
| `TOUR_API_KEY` | 한국관광공사 Tour API |
| `OLLAMA_HOST` / `LLM_MODEL` | 로컬 LLM(Ollama) 엔드포인트·모델. 프로덕션 연결: [프로덕션 Ollama](ollama-production.md) |

## 프로덕션 보안

- `DEBUG=False`일 때 기본 `SECRET_KEY`를 그대로 쓰면 앱이 시작 시 **오류**를 냅니다.
- 세션 쿠키: `HttpOnly`, `SameSite=Lax`, `SESSION_COOKIE_SECURE`는 환경으로 제어합니다.
- OAuth 자격 증명이 없어도 앱은 기동됩니다. 설정된 공급자만 로그인 버튼이 표시됩니다.

## 시크릿 생성 예시

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

OAuth 콘솔 설정은 [OAuth 설정](oauth.md)을 참고하세요.
