# Gabojago (가보자고)

<p align="right">
  <a href="./README.md">한국어</a> ·
  <strong>English</strong>
</p>

A Flask web application for Korean tourism information, reviews, and course recommendations. Browse spots by region and category, integrate with the Tour API, and sign in with username/password or Google/Kakao OAuth in Korean or English.

**Full documentation:** [docs/en/README.md](docs/en/README.md)

## Key capabilities

- Popular spots, regional exploration, and detail pages
- User reviews with filtering and sorting
- Course pages via the Tour API and (with local Ollama) AI course suggestions
- Username/password plus Google and Kakao OIDC sign-in
- Korean/English UI via Flask-Babel
- Admin direct database management (admin accounts)

## Technology stack

| Area | Technology |
| --- | --- |
| Backend | Flask 3, Jinja2 |
| Database | MongoDB (PyMongo) |
| Auth | Sessions + Authlib OAuth |
| UI | MDB UI Kit, Font Awesome, custom CSS |
| i18n | Flask-Babel |
| External APIs | Korea Tourism Organization Tour API, (optional) Ollama |

## Architecture overview

```
app.py              # Application factory, indexes, blueprints
config.py           # Environment config and validation
extensions/         # MongoDB, OAuth, i18n
routes/             # HTTP blueprints
models/             # Data access
services/           # Tour API, LLM, auth, migrations
templates/          # SSR templates and macros
static/             # CSS, JS, uploads
translations/       # Babel catalogs
```

## Quick start

```bash
python -m venv venv
.\venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.example .env             # edit values
# MongoDB → docs/en/mongodb.md
python app.py
```

Open `http://127.0.0.1:5000`

## Configuration

Set `SECRET_KEY`, `MONGO_URI`, and optional OAuth/Tour API/Ollama values from `.env.example`. Only configured integrations are enabled.

→ [Configuration](docs/en/configuration.md)

## OAuth

Register redirect URIs and Kakao allowed IPs for each environment.

→ [OAuth setup](docs/en/oauth.md)

## Localization

Extract and compile Babel catalogs after changing UI strings.

→ [Localization](docs/en/localization.md)

## Testing

```bash
pip install -r requirements-dev.txt
ruff check .
pytest -q
```

→ [Testing](docs/en/testing.md)

## Security

- `DEBUG=False` and a dedicated `SECRET_KEY` required in production
- OAuth links only provider-verified emails
- Session rotation on login with locale preserved
- Open-redirect protection (`services/redirect_safety.py`)

## Deployment

Free-tier overview (Render + Atlas): [Deployment](docs/en/deployment.md)

## Documentation

| Topic | Link |
| --- | --- |
| Local setup | [docs/en/setup.md](docs/en/setup.md) |
| MongoDB | [docs/en/mongodb.md](docs/en/mongodb.md) |
| Configuration | [docs/en/configuration.md](docs/en/configuration.md) |
| OAuth | [docs/en/oauth.md](docs/en/oauth.md) |
| i18n | [docs/en/localization.md](docs/en/localization.md) |
| Migrations | [docs/en/migrations.md](docs/en/migrations.md) |
| Testing | [docs/en/testing.md](docs/en/testing.md) |
| Deployment | [docs/en/deployment.md](docs/en/deployment.md) |
