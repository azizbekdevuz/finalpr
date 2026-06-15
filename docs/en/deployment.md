# Deployment

<p align="right">
  <a href="../ko/deployment.md">한국어</a> ·
  <strong>English</strong>
</p>

## Production checklist

| Item | Recommended |
| --- | --- |
| `DEBUG` | `False` |
| `SECRET_KEY` | Strong random value |
| `SESSION_COOKIE_SECURE` | `True` |
| `PREFERRED_URL_SCHEME` | `https` |
| WSGI | Gunicorn or similar (not the Flask dev server) |
| Database | Managed MongoDB (e.g. MongoDB Atlas) |

## Free-tier example stack

| Component | Service |
| --- | --- |
| App hosting | [Render](https://render.com) free web service |
| Database | [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) M0 |
| Domain | `*.onrender.com` subdomain |

### Example WSGI entry

`wsgi.py`:

```python
from app import create_app
app = create_app()
```

Start command:

```bash
gunicorn --bind 0.0.0.0:$PORT --workers 2 wsgi:app
```

Add `gunicorn` to `requirements.txt`.

## Limitations

- **Ollama** usually cannot run on free PaaS; AI course features may appear offline.
- `static/uploads` may use ephemeral disk and be lost on redeploy.
- Register production OAuth callback URLs and Kakao allowed IPs.

See [Configuration](configuration.md) and [OAuth setup](oauth.md).
