from __future__ import annotations

import json
import os
from typing import Any

from flask import Blueprint, flash, redirect, render_template, session, url_for
from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l

import models.review as ReviewModel
import models.saved_course as SavedCourseModel
from extensions.db import mongo
from services.tour_api import fetch_detail_common

main_bp = Blueprint('main', __name__)

# ── Region exploration data (region names are place data; kept in Korean) ─────
_REGION_SPOTS_PATH = os.path.join(os.path.dirname(__file__), '..', 'region_spots_final.json')
try:
    with open(_REGION_SPOTS_PATH, encoding='utf-8') as _f:
        REGION_SPOTS_DATA: dict[str, Any] = json.load(_f)
except OSError:
    REGION_SPOTS_DATA = {}

REGIONS_ORDER = ['서울', '제주', '부산', '강릉', '인천', '경주', '해운대', '가평', '여수', '속초']

# Region marketing copy is application-owned UI text -> localized lazily so the
# strings are resolved per request in the active locale.
REGION_META: dict[str, dict[str, Any]] = {
    '서울':   {'icon': 'fa-solid fa-city', 'desc': _l('A city of ten million where palaces, night views and food meet')},
    '제주':   {'icon': 'fa-solid fa-leaf', 'desc': _l('An island of volcanic scenery and emerald seas')},
    '부산':   {'icon': 'fa-solid fa-water', 'desc': _l('A port city of sea, mountains and soulful alleys')},
    '강릉':   {'icon': 'fa-solid fa-sun', 'desc': _l('A coastal city of Jeongdongjin sunrises and Gyeongpo beaches')},
    '인천':   {'icon': 'fa-solid fa-plane', 'desc': _l('A port city of islands and Chinatown')},
    '경주':   {'icon': 'fa-solid fa-landmark', 'desc': _l('A historic city where a thousand years of Silla still breathe')},
    '해운대': {'icon': 'fa-solid fa-umbrella-beach', 'desc': _l("Busan's landmark and Korea's signature beach")},
    '가평':   {'icon': 'fa-solid fa-campground', 'desc': _l('A healing getaway near the capital: Cheongpyeong Lake and Jara Island')},
    '여수':   {'icon': 'fa-solid fa-ship', 'desc': _l('A romantic port city of night seas and turtle ships')},
    '속초':   {'icon': 'fa-solid fa-mountain', 'desc': _l('A pristine coastal city where Seoraksan meets the East Sea')},
}

# Carousel captions for the top-10 popular spots (application-owned UI copy).
CAROUSEL_DESC = [
    _l('A convention center leading the MICE industry'),
    _l('A real-world Evertopia that creates happy energy'),
    _l("Korea's largest international exhibition and convention center"),
    _l("A park with the world's longest bridge fountain"),
    _l('Full of adventure and wonder!'),
    _l('A moving space where past, present and future coexist'),
    _l('A restful space rich with sights and things to enjoy'),
    _l('A park to enjoy in many ways all year round'),
    _l('Historic ruins preserving the beauty of Silla Buddhist culture'),
    _l('A beach with a crescent-shaped white-sand shore'),
]


def get_firstimage_from_api(contentid: str | None) -> str:
    """Fetch a spot's first image via the Tour API (no duplicated API key)."""
    if not contentid:
        return ''
    common = fetch_detail_common(str(contentid))
    return common.get('firstimage', '') if common else ''


def _build_region_cards(include_spots: bool) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for region in REGIONS_ORDER:
        meta = REGION_META.get(region, {'icon': 'fa-solid fa-location-dot', 'desc': ''})
        card: dict[str, Any] = {
            'name': region,
            'icon': meta['icon'],
            'desc': meta['desc'],
        }
        if include_spots:
            info = REGION_SPOTS_DATA.get(region, {})
            raw_spots = info.get('spots', [])
            card['total'] = info.get('count', len(raw_spots))
            card['spots'] = raw_spots
        cards.append(card)
    return cards


@main_bp.route('/')
def index():
    """Home page: hero carousel + region explorer + recent reviews + CTA."""
    popular_spots = list(mongo.db.popular_spots.find({'rank': {'$lte': 10}}).sort('rank', 1))
    fallback_img = (
        'https://images.unsplash.com/photo-1540206351-d6465b3ac5c1?q=80&w=1600&auto=format&fit=crop'
    )
    carousel_spots = []
    for i, spot in enumerate(popular_spots):
        if i >= len(CAROUSEL_DESC):
            break
        contentid = spot.get('contentid')
        image_url = spot.get('firstimage') or ''
        if not image_url:
            image_url = get_firstimage_from_api(contentid) or fallback_img
        name = spot.get('name')
        if name == '롯데월드잠실점':
            name = '롯데월드 어드벤처'
        carousel_spots.append({
            'name': name,
            'desc': CAROUSEL_DESC[i],
            'image': image_url,
            'contentid': contentid,
            'region': spot.get('addr1', '').split()[0] if spot.get('addr1') else _('Korea'),
        })

    recent_reviews = ReviewModel.get_recent_reviews(limit=3)
    for r in recent_reviews:
        if r.get('spot_id'):
            spot = mongo.db.tourist_spots.find_one({'_id': r['spot_id']})
            r['spot_name'] = spot.get('name') if spot else _('Deleted spot')
        else:
            r['spot_name'] = r.get('spot_name') or _('Unknown spot')

    return render_template('index.html',
                           carousel_spots=carousel_spots,
                           recent_reviews=recent_reviews,
                           region_data=_build_region_cards(include_spots=False))


@main_bp.route('/dashboard')
def dashboard():
    """My page: the signed-in user's review history."""
    if 'user_id' not in session:
        flash(_('Please sign in to continue.'), 'warning')
        return redirect(url_for('auth.login'))

    reviews = ReviewModel.get_reviews_by_user(session['user_id'])
    for r in reviews:
        if r.get('spot_id'):
            spot = mongo.db.tourist_spots.find_one({'_id': r['spot_id']}, {'name': 1})
            r['spot_name'] = spot['name'] if spot else _('Deleted spot')
        else:
            r['spot_name'] = r.get('spot_name') or _('Unknown spot')

    saved_course_count = SavedCourseModel.count_by_user(session['user_id'])
    return render_template('dashboard.html', reviews=reviews,
                           saved_course_count=saved_course_count)


@main_bp.route('/regions')
def regions():
    """Region explorer page (CSV-based rankings + public API images)."""
    return render_template('regions.html', region_data=_build_region_cards(include_spots=True))
