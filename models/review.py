from datetime import UTC, datetime

from bson import ObjectId

from extensions.db import mongo


def create_review(spot_id, user_id, username, rating, content):
    """리뷰를 생성합니다."""
    review = {
        'spot_id': ObjectId(spot_id),
        'user_id': ObjectId(user_id),
        'username': username,
        'rating': int(rating),
        'content': content,
        'created_at': datetime.now(UTC)
    }
    result = mongo.db.reviews.insert_one(review)
    return str(result.inserted_id)


def create_free_review(spot_name, user_id, username, rating, content):
    """관광지명을 자유 입력으로 받는 리뷰를 생성합니다 (spot_id 없음)."""
    review = {
        'spot_id':   None,
        'spot_name': spot_name.strip(),
        'user_id':   ObjectId(user_id),
        'username':  username,
        'rating':    int(rating),
        'content':   content,
        'created_at': datetime.now(UTC)
    }
    result = mongo.db.reviews.insert_one(review)
    return str(result.inserted_id)


def get_reviews_by_spot(spot_id):
    """특정 관광지의 모든 리뷰를 최신순으로 반환합니다."""
    return list(
        mongo.db.reviews
        .find({'spot_id': ObjectId(spot_id)})
        .sort('created_at', -1)
    )

def get_recent_reviews(limit=3):
    """모든 리뷰 중 최근 리뷰를 반환합니다."""
    return list(mongo.db.reviews.find().sort('created_at', -1).limit(limit))


def get_reviews_by_user(user_id):
    """특정 사용자의 모든 리뷰를 최신순으로 반환합니다."""
    return list(
        mongo.db.reviews
        .find({'user_id': ObjectId(user_id)})
        .sort('created_at', -1)
    )


def get_review_by_id(review_id):
    return mongo.db.reviews.find_one({'_id': ObjectId(review_id)})


def delete_review(review_id):
    mongo.db.reviews.delete_one({'_id': ObjectId(review_id)})


def user_already_reviewed(spot_id, user_id):
    """사용자가 이미 해당 관광지에 리뷰를 작성했는지 확인합니다."""
    return mongo.db.reviews.find_one({
        'spot_id': ObjectId(spot_id),
        'user_id': ObjectId(user_id)
    }) is not None
