import os
from flask import Flask
from config import Config
from extensions.db import mongo

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 업로드 폴더 생성
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # MongoDB 초기화
    mongo.init_app(app)

    # 인덱스 생성 (중복 방지)
    with app.app_context():
        mongo.db.users.create_index('username', unique=True)
        mongo.db.users.create_index('email', unique=True)
        mongo.db.tourist_spots.create_index('name')
        mongo.db.tourist_spots.create_index('region')
        mongo.db.tourist_spots.create_index('category')
        mongo.db.popular_spots.create_index('rank',      unique=True)
        mongo.db.popular_spots.create_index('contentid')
        mongo.db.saved_courses.create_index('user_id')
        mongo.db.saved_courses.create_index('created_at')

    # 블루프린트 등록
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.spots import spots_bp
    from routes.courses import courses_bp
    from routes.reviews import reviews_bp
    from routes.admin import admin_bp

    app.register_blueprint(main_bp,      url_prefix='/')
    app.register_blueprint(auth_bp,      url_prefix='/auth')
    app.register_blueprint(spots_bp,     url_prefix='/spots')
    app.register_blueprint(courses_bp,   url_prefix='/courses')
    app.register_blueprint(reviews_bp,   url_prefix='/reviews')
    app.register_blueprint(admin_bp,     url_prefix='/admin')

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
