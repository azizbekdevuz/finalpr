from datetime import datetime, timezone
from extensions.db import mongo
from bson import ObjectId


def create_spot(name, category, region, description, address, image_url, created_by):
    """관광지를 생성하고 삽입된 ID를 반환합니다."""
    spot = {
        'name': name,
        'category': category,
        'region': region,
        'description': description,
        'address': address,
        'image_url': image_url,
        'rating_avg': 0.0,
        'review_count': 0,
        'created_by': created_by,
        'created_at': datetime.now(timezone.utc)
    }
    result = mongo.db.tourist_spots.insert_one(spot)
    return str(result.inserted_id)


def get_all_spots(filters=None, sort_by='created_at', page=1, per_page=9):
    """관광지 목록 조회 (필터, 정렬, 페이지네이션)."""
    query = {}
    if filters:
        if filters.get('category'):
            query['category'] = filters['category']
        if filters.get('region'):
            query['region'] = filters['region']
        if filters.get('search'):
            query['name'] = {'$regex': filters['search'], '$options': 'i'}

    sort_order = -1 if sort_by in ('created_at', 'rating_avg') else 1
    skip = (page - 1) * per_page

    total = mongo.db.tourist_spots.count_documents(query)
    spots = list(
        mongo.db.tourist_spots
        .find(query)
        .sort(sort_by, sort_order)
        .skip(skip)
        .limit(per_page)
    )
    return spots, total


def get_spot_by_id(spot_id):
    return mongo.db.tourist_spots.find_one({'_id': ObjectId(spot_id)})


def update_spot(spot_id, data):
    """관광지 정보를 수정합니다."""
    mongo.db.tourist_spots.update_one(
        {'_id': ObjectId(spot_id)},
        {'$set': data}
    )


def delete_spot(spot_id):
    """관광지와 관련 리뷰를 삭제합니다."""
    mongo.db.tourist_spots.delete_one({'_id': ObjectId(spot_id)})
    mongo.db.reviews.delete_many({'spot_id': ObjectId(spot_id)})


def recalculate_rating(spot_id):
    """리뷰 수정 후 평균 평점을 재계산합니다."""
    pipeline = [
        {'$match': {'spot_id': ObjectId(spot_id)}},
        {'$group': {'_id': None, 'avg': {'$avg': '$rating'}, 'count': {'$sum': 1}}}
    ]
    result = list(mongo.db.reviews.aggregate(pipeline))
    if result:
        avg = round(result[0]['avg'], 1)
        count = result[0]['count']
    else:
        avg = 0.0
        count = 0

    mongo.db.tourist_spots.update_one(
        {'_id': ObjectId(spot_id)},
        {'$set': {'rating_avg': avg, 'review_count': count}}
    )


CATEGORIES = ['자연', '문화/역사', '음식/맛집', '액티비티', '쇼핑']
REGIONS = ['서울', '부산', '제주', '경주', '강원', '전주', '인천', '대구', '광주', '기타']
