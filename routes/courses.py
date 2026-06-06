"""Course pages, AI recommendation API, and saved courses."""

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



@courses_bp.route('/')
def courses():
    """Course page with optional AI chat UI."""
    return render_template('courses.html')


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

    first_spot = fetch_first_spot_by_keyword(keyword)

    if not first_spot:
        return jsonify({
            'ok': False,
            'error': _('No spot found for "%(keyword)s". Try another place.', keyword=keyword),
        }), 404

    mapx = first_spot.get('mapx', '')
    mapy = first_spot.get('mapy', '')

    nearby_spots = []
    if mapx and mapy:
        nearby_spots = fetch_nearby(
            mapx=mapx,
            mapy=mapy,
            content_type_id='12',
            radius=10000,
            count=2,
            exclude_content_id=str(first_spot.get('contentid', '')),
        )

    # Widen search radius when nearby results are sparse. / 주변 결과가 부족하면 검색 반경을 넓힙니다.
    if len(nearby_spots) < 2 and mapx and mapy:
        nearby_spots = fetch_nearby(
            mapx=mapx,
            mapy=mapy,
            content_type_id='12',
            radius=20000,
            count=2,
            exclude_content_id=str(first_spot.get('contentid', '')),
        )

    all_spots = [first_spot] + list(nearby_spots[:2])
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


@courses_bp.route('/llm-status')
def llm_status():
    """Return Ollama availability and configured model."""
    status = check_ollama_status()
    return jsonify(status)


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


@courses_bp.route('/my')
@login_required
def my_courses():
    """Saved courses for the signed-in member."""
    user_id = session['user_id']
    courses  = SavedCourseModel.get_courses_by_user(user_id)

    for c in courses:
        c['_id'] = str(c['_id'])

    return render_template('my_courses.html', courses=courses)


@courses_bp.route('/delete/<course_id>', methods=['POST'])
@login_required
def delete_course(course_id):
    """Delete a saved course owned by the current user."""
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

