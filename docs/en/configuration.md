# Configuration

<p align="right">
  <a href="../ko/configuration.md">한국어</a> ·
  <strong>English</strong>
</p>

Copy `.env.example` to `.env` and fill in real values. **Never commit secrets.**

## Variables

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Flask session signing key. Required in production. |
| `DEBUG` | `True`/`False`. Use `False` in production. |
| `MONGO_URI` | MongoDB connection string |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Google OAuth |
| `KAKAO_CLIENT_ID` / `KAKAO_CLIENT_SECRET` | Kakao REST API key (and optional secret) |
| `SESSION_COOKIE_SECURE` | `True` on HTTPS production; `False` for local HTTP |
| `PREFERRED_URL_SCHEME` | Use `https` in production |
| `TOUR_API_KEY` | Korea Tourism Organization Tour API |
| `OLLAMA_HOST` / `LLM_MODEL` | Local LLM (Ollama) endpoint and model. Production setup: [Ollama in production](ollama-production.md) |

## Production security

- With `DEBUG=False`, the app **refuses to start** if `SECRET_KEY` is still the development default.
- Session cookies use `HttpOnly`, `SameSite=Lax`; `SESSION_COOKIE_SECURE` is environment-controlled.
- The app boots without OAuth credentials; only configured providers show sign-in buttons.

## Generate a secret

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

See [OAuth setup](oauth.md) for provider console configuration.
