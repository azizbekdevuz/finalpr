import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    """Read a boolean flag from the environment ('1'/'true'/'yes')."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {'1', 'true', 'yes', 'on'}


class Config:
    # ── Flask ─────────────────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = _env_bool('DEBUG', True)

    # ── MongoDB ───────────────────────────────────────────────────────────────
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/tourism_db')

    # ── Upload ────────────────────────────────────────────────────────────────
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    # ── Local LLM (Ollama) ──────────────────────────────────────────────────────
    OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
    LLM_MODEL = os.environ.get('LLM_MODEL', 'qwen2.5:3b')

    # ── Localization (Flask-Babel) ──────────────────────────────────────────────
    BABEL_DEFAULT_LOCALE = 'ko'
    BABEL_DEFAULT_TIMEZONE = 'Asia/Seoul'
    BABEL_TRANSLATION_DIRECTORIES = 'translations'
    SUPPORTED_LOCALES = ('ko', 'en')

    # ── OAuth / OIDC providers (read from environment only) ──────────────────────
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    KAKAO_CLIENT_ID = os.environ.get('KAKAO_CLIENT_ID', '')
    KAKAO_CLIENT_SECRET = os.environ.get('KAKAO_CLIENT_SECRET', '')

    # ── Session cookie hardening ──────────────────────────────────────────────────
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    # Enable Secure cookies only when running behind HTTPS (production). Keeping
    # this False by default avoids breaking local HTTP development.
    SESSION_COOKIE_SECURE = _env_bool('SESSION_COOKIE_SECURE', False)
    PERMANENT_SESSION_LIFETIME = timedelta(days=14)
    PREFERRED_URL_SCHEME = os.environ.get('PREFERRED_URL_SCHEME', 'http')


def validate_runtime_config(app) -> None:
    """Fail loudly when a production deployment is missing a real secret key.

    In debug/development the bundled placeholder key is tolerated; in production
    (debug disabled) an explicit ``SECRET_KEY`` is mandatory.
    """
    insecure_default = 'dev-secret-key-change-in-production'
    if not app.debug and app.config.get('SECRET_KEY') == insecure_default:
        app.logger.critical(
            'SECRET_KEY is using the insecure development default while DEBUG is '
            'off. Set a strong SECRET_KEY environment variable before deploying.'
        )
        raise RuntimeError('A dedicated SECRET_KEY is required when DEBUG is disabled.')
