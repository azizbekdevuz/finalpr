# Local setup

<p align="right">
  <a href="../ko/setup.md">한국어</a> ·
  <strong>English</strong>
</p>

## Requirements

- Python 3.11+ recommended
- MongoDB (local or [MongoDB Atlas](https://www.mongodb.com/cloud/atlas))
- (Optional) Ollama — AI course recommendations

## Virtual environment and packages

```bash
python -m venv venv

# Windows
.\venv\Scripts\activate

# macOS / Linux
# source venv/bin/activate

pip install -r requirements.txt
```

For development tooling (pytest, ruff, mypy):

```bash
pip install -r requirements-dev.txt
```

## Environment file

```bash
cp .env.example .env
```

See [Configuration](configuration.md) for variable descriptions. Never commit `.env`.

## Database

Prepare MongoDB, then follow [MongoDB setup](mongodb.md) to configure `tourism_db`.

## Run the app

```bash
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

Use a WSGI server such as Gunicorn in production — see [Deployment](deployment.md).
