"""
models/saved_course.py
AI 추천 코스 저장 모델 (MongoDB: saved_courses 컬렉션)

Document 구조:
{
    _id:        ObjectId,
    user_id:    ObjectId,           -- 저장한 회원
    keyword:    str,                -- 검색 키워드 (예: "경복궁")
    spots: [                        -- 3개 관광지 정보
        {
            contentid: str,
            title:     str,
            addr1:     str,
            firstimage:str,
            overview:  str,
        }, ...
    ],
    summary:    str,                -- LLM 코스 요약
    description:str,                -- LLM 상세 설명
    model:      str,                -- 사용한 LLM 모델명
    created_at: datetime,
}
"""

from datetime import UTC, datetime

from bson import ObjectId

from extensions.db import mongo


def save_course(user_id: str, keyword: str, spots: list,
                summary: str, description: str, model: str) -> str:
    """AI 추천 코스를 저장합니다."""
    doc = {
        'user_id':     ObjectId(user_id),
        'keyword':     keyword,
        'spots':       spots,
        'summary':     summary,
        'description': description,
        'model':       model,
        'created_at':  datetime.now(UTC),
    }
    result = mongo.db.saved_courses.insert_one(doc)
    return str(result.inserted_id)


def get_courses_by_user(user_id: str) -> list:
    """특정 사용자의 저장 코스를 최신순으로 반환합니다."""
    return list(
        mongo.db.saved_courses
        .find({'user_id': ObjectId(user_id)})
        .sort('created_at', -1)
    )


def get_course_by_id(course_id: str) -> dict | None:
    """단일 저장 코스를 반환합니다."""
    try:
        return mongo.db.saved_courses.find_one({'_id': ObjectId(course_id)})
    except Exception:
        return None


def delete_course(course_id: str, user_id: str) -> bool:
    """
    저장 코스를 삭제합니다.
    본인 소유 코스만 삭제 가능.
    """
    result = mongo.db.saved_courses.delete_one({
        '_id':     ObjectId(course_id),
        'user_id': ObjectId(user_id),
    })
    return result.deleted_count > 0


def count_by_user(user_id: str) -> int:
    """사용자의 저장 코스 수를 반환합니다."""
    return mongo.db.saved_courses.count_documents({'user_id': ObjectId(user_id)})
