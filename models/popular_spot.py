"""
models/popular_spot.py
popular_spots 컬렉션 접근 함수
"""
from extensions.db import mongo


def get_all_popular(page: int = 1, per_page: int = 12) -> dict:
    """
    인기순 관광지 목록 (rank 오름차순)
    Returns:
        {
            'spots': [...],
            'total': int,
            'page': int,
            'per_page': int,
            'total_pages': int,
        }
    """
    total = mongo.db.popular_spots.count_documents({})
    skip  = (page - 1) * per_page

    spots = list(
        mongo.db.popular_spots
        .find({}, {'_id': 0})          # _id 제외
        .sort('rank', 1)                # rank 오름차순
        .skip(skip)
        .limit(per_page)
    )

    return {
        'spots':       spots,
        'total':       total,
        'page':        page,
        'per_page':    per_page,
        'total_pages': max(1, (total + per_page - 1) // per_page),
    }


def get_popular_by_contentid(content_id: str) -> dict | None:
    """contentid로 인기순 데이터 조회."""
    return mongo.db.popular_spots.find_one(
        {'contentid': str(content_id)},
        {'_id': 0}
    )
