from datetime import datetime, timezone
from extensions.db import mongo
from bson import ObjectId


def create_entry(user_id, username, rating, content):
    """방명록 글을 작성합니다."""
    entry = {
        'user_id':    ObjectId(user_id),
        'username':   username,
        'rating':     int(rating),
        'content':    content,
        'created_at': datetime.now(timezone.utc),
    }
    result = mongo.db.guestbook.insert_one(entry)
    return str(result.inserted_id)


def get_entries(page=1, per_page=10):
    """방명록 글 목록 (최신순, 페이지네이션)."""
    skip = (page - 1) * per_page
    entries = list(
        mongo.db.guestbook
        .find()
        .sort('created_at', -1)
        .skip(skip)
        .limit(per_page)
    )
    total = mongo.db.guestbook.count_documents({})
    return entries, total


def get_entry_by_id(entry_id):
    return mongo.db.guestbook.find_one({'_id': ObjectId(entry_id)})


def delete_entry(entry_id):
    mongo.db.guestbook.delete_one({'_id': ObjectId(entry_id)})


def get_stats():
    """전체 평균 별점 + 총 작성 수를 반환합니다."""
    pipeline = [
        {
            '$group': {
                '_id':        None,
                'avg_rating': {'$avg': '$rating'},
                'count':      {'$sum': 1},
            }
        }
    ]
    result = list(mongo.db.guestbook.aggregate(pipeline))
    if result:
        return {
            'avg_rating': round(result[0]['avg_rating'], 1),
            'count':      result[0]['count'],
        }
    return {'avg_rating': 0, 'count': 0}


def user_already_wrote_today(user_id):
    """오늘 이미 작성한 글이 있는지 확인합니다 (하루 1회 제한)."""
    from datetime import date
    today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)
    return mongo.db.guestbook.find_one({
        'user_id':    ObjectId(user_id),
        'created_at': {'$gte': today_start},
    }) is not None
