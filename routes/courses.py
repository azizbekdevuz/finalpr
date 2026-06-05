"""
routes/courses.py
추천 코스 페이지 + AI 코스 추천 AJAX API + 저장 기능

Endpoints:
  GET  /courses/              — 정적 코스 카드 + AI 채팅 UI 페이지
  POST /courses/ai-recommend  — AI 코스 추천 JSON API
  GET  /courses/llm-status    — Ollama 상태 확인
  POST /courses/save          — AI 추천 코스 저장 (로그인 필요)
  GET  /courses/my            — 내 저장 코스 목록 (로그인 필요)
  POST /courses/delete/<id>   — 저장 코스 삭제 (본인만)
"""

from flask import Blueprint, jsonify, render_template, request, session
from flask_babel import get_locale
from flask_babel import gettext as _

import models.saved_course as SavedCourseModel
from routes import login_required
from services.llm_service import check_ollama_status, extract_place, generate_course_description
from services.tour_api import (
    fetch_detail_common,
    fetch_first_spot_by_keyword,
    fetch_nearby,
)

courses_bp = Blueprint('courses', __name__)



# ── GET /courses/ ─────────────────────────────────────────────────────────────

@courses_bp.route('/')
def courses():
    """추천 코스 페이지 (AI 채팅 UI)."""
    return render_template('courses.html')


# ── POST /courses/ai-recommend ───────────────────────────────────────────────

@courses_bp.route('/ai-recommend', methods=['POST'])
def ai_recommend():
    """AI course recommendation AJAX API.

    Request JSON: {"message": "..."}
    Response JSON: {"ok", "keyword", "spots", "summary", "description", "model"}
    or {"ok": false, "error": "..."} on failure. Response language follows the
    active locale.
    """
    from flask import current_app

    data    = request.get_json(silent=True) or {}
    message = data.get('message', '').strip()

    if not message:
        return jsonify({'ok': False, 'error': _('Please enter a message.')}), 400

    locale = str(get_locale() or 'ko')

    # ── Step 1: LLM → place keyword extraction ──────────────────────────────
    keyword = extract_place(message)

    if keyword == '__OLLAMA_OFFLINE__':
        return jsonify({
            'ok': False,
            'error': _('Cannot reach the Ollama server. Start it with `ollama serve` first.'),
        }), 503

    if not keyword:
        return jsonify({
            'ok': False,
            'error': _('We could not find a place to visit. Try e.g. "I want to visit Gyeongbokgung".'),
        }), 400

    # ── Step 2: searchKeyword2 → contentid 최솟값 관광지 선택 ────────────────
    first_spot = fetch_first_spot_by_keyword(keyword)

    if not first_spot:
        return jsonify({
            'ok': False,
            'error': _('No spot found for "%(keyword)s". Try another place.', keyword=keyword),
        }), 404

    # ── Step 3: locationBasedList2 → 주변 관광지 2개 선택 ────────────────────
    mapx = first_spot.get('mapx', '')
    mapy = first_spot.get('mapy', '')

    nearby_spots = []
    if mapx and mapy:
        nearby_spots = fetch_nearby(
            mapx=mapx,
            mapy=mapy,
            content_type_id='12',   # 관광지
            radius=10000,           # 10km 반경
            count=2,
            exclude_content_id=str(first_spot.get('contentid', '')),
        )

    # 주변 관광지가 부족하면 반경 확대 재시도
    if len(nearby_spots) < 2 and mapx and mapy:
        nearby_spots = fetch_nearby(
            mapx=mapx,
            mapy=mapy,
            content_type_id='12',
            radius=20000,   # 20km 반경으로 확대
            count=2,
            exclude_content_id=str(first_spot.get('contentid', '')),
        )

    # 3개 관광지 목록 구성
    all_spots = [first_spot] + list(nearby_spots[:2])

    # ── Step 4: detailCommon2 → 각 관광지 overview 추출 ──────────────────────
    enriched_spots = []
    overviews      = []

    for spot in all_spots:
        cid    = str(spot.get('contentid', ''))
        common = fetch_detail_common(cid) if cid else {}

        overview = common.get('overview', '') or ''
        overviews.append(overview)

        enriched_spots.append({
            'contentid':  cid,
            'title':      spot.get('title') or common.get('title', ''),
            'addr1':      spot.get('addr1') or common.get('addr1', ''),
            'firstimage': spot.get('firstimage') or common.get('firstimage', ''),
            'mapx':       spot.get('mapx') or common.get('mapx', ''),
            'mapy':       spot.get('mapy') or common.get('mapy', ''),
            'overview':   overview[:300] + '…' if len(overview) > 300 else overview,
        })

    # ── Step 5: LLM → course summary + conversational description ───────────
    llm_result = generate_course_description(enriched_spots, overviews, locale=locale)

    model = current_app.config.get('LLM_MODEL', 'gemma4:26b')

    return jsonify({
        'ok':          True,
        'keyword':     keyword,
        'spots':       enriched_spots,
        'summary':     llm_result.get('summary', ''),
        'description': llm_result.get('description', ''),
        'model':       model,
    })


# ── GET /courses/llm-status ───────────────────────────────────────────────────

@courses_bp.route('/llm-status')
def llm_status():
    """Ollama 서버 상태 및 현재 모델 확인."""
    status = check_ollama_status()
    return jsonify(status)


# ── POST /courses/save ────────────────────────────────────────────────────────

@courses_bp.route('/save', methods=['POST'])
@login_required
def save_course():
    """Save an AI-recommended course to the member's saved courses.

    Request JSON: {"keyword", "spots", "summary", "description", "model"}
    Response JSON: {"ok": true, "course_id": "..."}
    """
    data = request.get_json(silent=True) or {}

    keyword     = data.get('keyword', '').strip()
    spots       = data.get('spots', [])
    summary     = data.get('summary', '').strip()
    description = data.get('description', '').strip()
    model       = data.get('model', '')

    if not keyword or not spots:
        return jsonify({'ok': False, 'error': _('There is no course data to save.')}), 400

    user_id = session['user_id']

    course_id = SavedCourseModel.save_course(
        user_id=user_id,
        keyword=keyword,
        spots=spots,
        summary=summary,
        description=description,
        model=model,
    )

    return jsonify({'ok': True, 'course_id': course_id})


# ── GET /courses/my ───────────────────────────────────────────────────────────

@courses_bp.route('/my')
@login_required
def my_courses():
    """내 저장 코스 목록 페이지."""
    user_id = session['user_id']
    courses  = SavedCourseModel.get_courses_by_user(user_id)

    # ObjectId → str 변환
    for c in courses:
        c['_id'] = str(c['_id'])

    return render_template('my_courses.html', courses=courses)


# ── POST /courses/delete/<course_id> ─────────────────────────────────────────

@courses_bp.route('/delete/<course_id>', methods=['POST'])
@login_required
def delete_course(course_id):
    """저장된 코스를 삭제합니다 (본인 소유만)."""
    user_id = session['user_id']
    deleted  = SavedCourseModel.delete_course(course_id, user_id)

    if request.is_json:
        return jsonify({'ok': deleted})

    from flask import flash, redirect, url_for
    if deleted:
        flash(_('The course has been deleted.'), 'success')
    else:
        flash(_('This course could not be deleted.'), 'danger')
    return redirect(url_for('courses.my_courses'))

