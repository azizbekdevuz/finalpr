from __future__ import annotations

import os
from typing import Any

from flask import Flask
from flask_babel import get_locale
from pymongo.errors import PyMongoError

from config import Config, validate_runtime_config
from extensions.db import mongo
from extensions.i18n import LANGUAGE_NAMES, init_i18n
from extensions.oauth import SUPPORTED_PROVIDERS, init_oauth, provider_configured


def create_app(config_object: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)

    validate_runtime_config(app)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # ── Extensions ──────────────────────────────────────────────────────────
    mongo.init_app(app)
    init_oauth(app)
    init_i18n(app)

    _ensure_indexes(app)
    _register_blueprints(app)
    _register_context_processors(app)
    _register_cli(app)

    return app


def _ensure_indexes(app: Flask) -> None:
    """Create indexes idempotently. Never performs destructive migrations."""
    with app.app_context():
        try:
            mongo.db.users.create_index('username', unique=True)
            mongo.db.users.create_index('email', unique=True)
            # Non-unique helper index for normalized-email lookups. A unique
            # partial index is added only by the audited backfill command.
            mongo.db.users.create_index('email_normalized')
            mongo.db.tourist_spots.create_index('name')
            mongo.db.tourist_spots.create_index('region')
            mongo.db.tourist_spots.create_index('category')
            mongo.db.popular_spots.create_index('rank', unique=True)
            mongo.db.popular_spots.create_index('contentid')
            mongo.db.saved_courses.create_index('user_id')
            mongo.db.saved_courses.create_index('created_at')
            mongo.db.oauth_identities.create_index(
                [('provider', 1), ('subject', 1)], unique=True
            )
            mongo.db.oauth_identities.create_index('user_id')
            mongo.db.oauth_identities.create_index('provider_email')
        except PyMongoError as exc:  # pragma: no cover - depends on live MongoDB
            app.logger.error('Index creation skipped due to MongoDB error: %s', exc)


def _register_blueprints(app: Flask) -> None:
    from routes.admin import admin_bp
    from routes.auth import auth_bp
    from routes.courses import courses_bp
    from routes.language import language_bp
    from routes.main import main_bp
    from routes.oauth import oauth_bp
    from routes.reviews import reviews_bp
    from routes.spots import spots_bp

    app.register_blueprint(main_bp, url_prefix='/')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(oauth_bp, url_prefix='/auth/oauth')
    app.register_blueprint(language_bp, url_prefix='/language')
    app.register_blueprint(spots_bp, url_prefix='/spots')
    app.register_blueprint(courses_bp, url_prefix='/courses')
    app.register_blueprint(reviews_bp, url_prefix='/reviews')
    app.register_blueprint(admin_bp, url_prefix='/admin')


def _register_context_processors(app: Flask) -> None:
    @app.context_processor
    def inject_i18n() -> dict[str, Any]:
        default = app.config.get('BABEL_DEFAULT_LOCALE', 'ko')
        current = str(get_locale() or default)
        supported = app.config.get('SUPPORTED_LOCALES', ('ko', 'en'))
        return {
            'current_locale': current,
            'language_names': LANGUAGE_NAMES,
            'supported_languages': [(code, LANGUAGE_NAMES.get(code, code)) for code in supported],
        }

    @app.context_processor
    def inject_oauth() -> dict[str, Any]:
        return {
            'oauth_enabled': {p: provider_configured(p) for p in SUPPORTED_PROVIDERS},
        }


def _register_cli(app: Flask) -> None:
    from services.migrations import register_migration_commands
    register_migration_commands(app)


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
