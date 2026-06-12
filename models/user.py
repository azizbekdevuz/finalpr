from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from extensions.db import mongo
from bson import ObjectId


def create_user(username, email, password, role='user'):
    """새 사용자를 생성하고 삽입된 ID를 반환합니다."""
    hashed = generate_password_hash(password)
    user = {
        'username': username,
        'email': email,
        'password_hash': hashed,
        'role': role,
        'created_at': datetime.now(timezone.utc)
    }
    result = mongo.db.users.insert_one(user)
    return str(result.inserted_id)


def find_by_username(username):
    return mongo.db.users.find_one({'username': username})


def find_by_email(email):
    return mongo.db.users.find_one({'email': email})


def find_by_id(user_id):
    return mongo.db.users.find_one({'_id': ObjectId(user_id)})


def verify_password(user_doc, password):
    return check_password_hash(user_doc['password_hash'], password)


def username_exists(username):
    return mongo.db.users.find_one({'username': username}) is not None


def email_exists(email):
    return mongo.db.users.find_one({'email': email}) is not None
