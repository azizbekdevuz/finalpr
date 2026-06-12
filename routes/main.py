from flask import Blueprint, render_template, session
import models.spot as SpotModel
import models.review as ReviewModel
import models.saved_course as SavedCourseModel
from extensions.db import mongo
import json, os

main_bp = Blueprint('main', __name__)

# ── 지역별 관광지 데이터 (CSV + API 검색 결과) ─────────────────────────────────────
_REGION_SPOTS_PATH = os.path.join(os.path.dirname(__file__), '..', 'region_spots_final.json')
try:
    with open(_REGION_SPOTS_PATH, encoding='utf-8') as _f:
        REGION_SPOTS_DATA = json.load(_f)
except Exception:
    REGION_SPOTS_DATA = {}


import urllib.request
import json
from extensions.db import mongo

def get_firstimage_from_api(contentid):
    """TourAPI detailCommon2를 호출하여 firstimage를 가져옵니다."""
    if not contentid:
        return ""
    
    SERVICE_KEY = 'BiJFkUSMy+7rGFaSZz9T3l4B+ClKAsEFj0pk9OIkaH+8XhkmoVROvvIeKwNoEeg7/0gYT1hvCpSBqmOJfgWNfw=='
    url = f"http://apis.data.go.kr/B551011/KorService2/detailCommon2?serviceKey={SERVICE_KEY}&MobileOS=ETC&MobileApp=AppTest&_type=json&contentId={contentid}&defaultYN=Y&firstImageYN=Y"
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode('utf-8'))
            items = data.get('response', {}).get('body', {}).get('items', {})
            if items and items.get('item'):
                item_list = items['item']
                if not isinstance(item_list, list):
                    item_list = [item_list]
                return item_list[0].get('firstimage', '')
    except Exception:
        pass
    return ""

@main_bp.route('/')
def index():
    """메인 페이지: 상단 캐러셀 + 지역별 탐색 + 리뷰 목록 + 코스 만들기."""
    
    # ── 상단 캐러셀 데이터 (Top 1~10 인기 관광지) ──
    carousel_desc = [
        "마이스 산업을 리드하는 컨벤션센터",
        "행복 에너지를 만드는 현실 속 에버토피아",
        "국내 최대의 규모를 자랑하는 국제적 전시 컨벤션 센터",
        "세계에서 가장 긴 교량분수가 있는 공원",
        "모험과 신비로움이 가득!",
        "과거와 현재, 미래가 공존하는 감동의 공간",
        "볼거리와 즐길거리가 풍부한 휴식공간",
        "사계절 내내 다양하게 즐길 수 있는 공원",
        "신라 불교문화의 아름다움을 간직한 역사 유적",
        "초승달처럼 반원으로 생긴 백사장의 해변"
    ]
    
    popular_spots = list(mongo.db.popular_spots.find({"rank": {"$lte": 10}}).sort("rank", 1))
    carousel_spots = []
    
    for i, spot in enumerate(popular_spots):
        if i >= len(carousel_desc):
            break
            
        contentid = spot.get("contentid")
        fallback_img = "https://images.unsplash.com/photo-1540206351-d6465b3ac5c1?q=80&w=1600&auto=format&fit=crop"

        # DB에 firstimage 있으면 API 호출 없이 바로 사용
        image_url = spot.get("firstimage") or ""
        if not image_url:
            image_url = get_firstimage_from_api(contentid) or fallback_img
        
        name = spot.get("name")
        if name == "롯데월드잠실점":
            name = "롯데월드 어드벤처"
            
        carousel_spots.append({
            "name": name,
            "desc": carousel_desc[i],
            "image": image_url,
            "contentid": contentid,
            "region": spot.get("addr1", "").split()[0] if spot.get("addr1") else "대한민국"
        })

    # ── 최근 리뷰 ──
    recent_reviews = ReviewModel.get_recent_reviews(limit=3)
    for r in recent_reviews:
        if r.get('spot_id'):
            spot = mongo.db.tourist_spots.find_one({'_id': r['spot_id']})
            r['spot_name'] = spot.get('name') if spot else '삭제된 관광지'
        else:
            r['spot_name'] = r.get('spot_name', '알 수 없는 관광지')

    # ── 지역별 탐색 ──
    REGIONS_ORDER = ['서울', '제주', '부산', '강릉', '인천', '경주', '해운대', '가평', '여수', '속초']
    REGION_META = {
        '서울':  {'emoji': '🏙️', 'desc': '궁궐·야경·먹거리가 공존하는 천만 도시'},
        '제주':  {'emoji': '🌺', 'desc': '화산섬 절경과 에메랄드 바다의 섬'},
        '부산':  {'emoji': '🌊', 'desc': '바다와 산, 감성 골목의 항구 도시'},
        '강릉':  {'emoji': '🌊', 'desc': '정동진 일출과 경포 바다의 해변 도시'},
        '인천':  {'emoji': '✈️', 'desc': '섬과 차이나타운이 어우러진 항구 도시'},
        '경주':  {'emoji': '🏯', 'desc': '천년 신라의 숨결이 살아있는 역사 도시'},
        '해운대': {'emoji': '🏖️', 'desc': '부산의 랜드마크, 대한민국 대표 해수욕장'},
        '가평':  {'emoji': '🏕️', 'desc': '청평호·자라섬, 수도권 근교 힐링 여행지'},
        '여수':  {'emoji': '🦞', 'desc': '밤바다와 거북선의 낭만 항구 도시'},
        '속초':  {'emoji': '🏔️', 'desc': '설악산과 동해가 만나는 청정 해변 도시'},
    }
    region_data = []
    for region in REGIONS_ORDER:
        meta = REGION_META.get(region, {'emoji': '📍', 'desc': ''})
        region_data.append({
            'name': region,
            'emoji': meta['emoji'],
            'desc': meta['desc']
        })

    return render_template('index.html',
                           carousel_spots=carousel_spots,
                           recent_reviews=recent_reviews,
                           region_data=region_data)


@main_bp.route('/dashboard')
def dashboard():
    """마이페이지: 내가 쓴 리뷰 목록."""
    if 'user_id' not in session:
        from flask import redirect, url_for, flash
        flash('로그인이 필요합니다.', 'warning')
        return redirect(url_for('auth.login'))

    reviews = ReviewModel.get_reviews_by_user(session['user_id'])

    for r in reviews:
        if r.get('spot_id'):
            spot = mongo.db.tourist_spots.find_one(
                {'_id': r['spot_id']}, {'name': 1}
            )
            r['spot_name'] = spot['name'] if spot else '삭제된 관광지'
        else:
            r['spot_name'] = r.get('spot_name', '알 수 없는 관광지')

    saved_course_count = SavedCourseModel.count_by_user(session['user_id'])

    return render_template('dashboard.html', reviews=reviews,
                           saved_course_count=saved_course_count)


@main_bp.route('/regions')
def regions():
    """지역별 탐색 페이지 — CSV 기반 관광지 순위 + 공공 API 이미지."""
    REGIONS_ORDER = ['서울', '제주', '부산', '강릉', '인천', '경주', '해운대', '가평', '여수', '속초']

    REGION_META = {
        '서울':  {'emoji': '🏙️', 'desc': '궁궐·야경·먹거리가 공존하는 천만 도시'},
        '제주':  {'emoji': '🌺', 'desc': '화산섬 절경과 에메랄드 바다의 섬'},
        '부산':  {'emoji': '🌊', 'desc': '바다와 산, 감성 골목의 항구 도시'},
        '강릉':  {'emoji': '🌊', 'desc': '정동진 일출과 경포 바다의 해변 도시'},
        '인천':  {'emoji': '✈️', 'desc': '섬과 차이나타운이 어우러진 항구 도시'},
        '경주':  {'emoji': '🏯', 'desc': '천년 신라의 숨결이 살아있는 역사 도시'},
        '해운대': {'emoji': '🏖️', 'desc': '부산의 랜드마크, 대한민국 대표 해수욕장'},
        '가평':  {'emoji': '🏕️', 'desc': '청평호·자라섬, 수도권 근교 힐링 여행지'},
        '여수':  {'emoji': '🦞', 'desc': '밤바다와 거북선의 낭만 항구 도시'},
        '속초':  {'emoji': '🏔️', 'desc': '설악산과 동해가 만나는 청정 해변 도시'},
    }

    region_data = []
    for region in REGIONS_ORDER:
        region_info = REGION_SPOTS_DATA.get(region, {})
        raw_spots   = region_info.get('spots', [])
        total_count = region_info.get('count', len(raw_spots))

        meta = REGION_META.get(region, {'emoji': '📍', 'desc': ''})
        region_data.append({
            'name':          region,
            'emoji':         meta['emoji'],
            'desc':          meta['desc'],
            'total':         total_count,
            'spots':         raw_spots,
        })

    return render_template('regions.html', region_data=region_data)

# Reload trigger
# Reload trigger 2
# Reload trigger 3
# Reload trigger 3
