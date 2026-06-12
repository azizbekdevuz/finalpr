from flask import (Blueprint, render_template, request,
                   redirect, url_for, session, flash)
from services.tour_api import (fetch_spots, ARRANGE_LATEST, ARRANGE_POPULAR, CONTENT_TYPE_MAP,
                               fetch_detail_common, fetch_detail_intro, fetch_detail_images,
                               fetch_nearby)
import models.spot as SpotModel
import models.review as ReviewModel
import models.popular_spot as PopularSpotModel
from routes import admin_required, login_required

spots_bp = Blueprint('spots', __name__)

# ── 공공 API 기반 목록 페이지 ──────────────────────────────────────────────────
@spots_bp.route('/')
def list_spots():
    """
    관광지 목록
    - 최신순: 공공 API (areaBasedSyncList2)
    - 인기순: MongoDB popular_spots 컬렉션 (엑셀 기반 고정 순위)
    페이지네이션: 12개씩
    """
    sort = request.args.get('sort', 'latest')   # 'latest' | 'popular'
    page = int(request.args.get('page', 1))

    if sort == 'popular':
        # ── 인기순: MongoDB에서 rank 오름차순 조회 ──────────────────────────
        result = PopularSpotModel.get_all_popular(page=page, per_page=12)
        # 카드 템플릿 호환을 위해 필드 보정 (date_str, mod_str 불필요하지만 키 통일)
        for item in result['spots']:
            item.setdefault('date_str', '')
            item.setdefault('mod_str', '')
    else:
        # ── 최신순: 공공 API ────────────────────────────────────────────────
        result = fetch_spots(page=page, per_page=12, arrange=ARRANGE_LATEST)
        for item in result['spots']:
            ct = item.get('createdtime', '')
            item['date_str'] = f"{ct[:4]}.{ct[4:6]}.{ct[6:8]}" if len(ct) >= 8 else ''
            mt = item.get('modifiedtime', '')
            item['mod_str']  = f"{mt[:4]}.{mt[4:6]}.{mt[6:8]}" if len(mt) >= 8 else ''

    resp = render_template(
        'spots/list.html',
        result=result,
        current_sort=sort,
    )
    from flask import make_response
    response = make_response(resp)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    return response


# ── 공공 API 기반 관광지 상세 ─────────────────────────────────────────────────────────
@spots_bp.route('/api/<content_id>')
def api_detail(content_id):
    """또 맹돌려 공공 API 기반 관광지 상세 페이지."""
    # 1) 공통 정보
    common = fetch_detail_common(content_id)
    if not common:
        flash('관광 정보를 불러오지 못했습니다.', 'danger')
        return redirect(url_for('spots.list_spots'))

    content_type_id = common.get('contenttypeid', '12')

    # 2) 소개 정보
    intro = fetch_detail_intro(content_id, content_type_id)

    # 3) 이미지 목록
    images = fetch_detail_images(content_id)

    # 유형 라벨 맵핑
    type_labels = {
        '12': '관광지', '14': '문화시설', '15': '축제/공연',
        '25': '여행코스', '28': '레포츠', '32': '숙박',
        '38': '쇼핑', '39': '음식점',
    }

    # 4) GPS 좌표 기반 근처 관광지 & 음식점 (거리순, 각 3개)
    nearby_spots       = []
    nearby_restaurants = []
    if common.get('mapx') and common.get('mapy'):
        nearby_spots = fetch_nearby(
            mapx=common['mapx'],
            mapy=common['mapy'],
            content_type_id='12',   # 관광지
            radius=5000,
            count=3,
            exclude_content_id=content_id,
        )
        nearby_restaurants = fetch_nearby(
            mapx=common['mapx'],
            mapy=common['mapy'],
            content_type_id='39',   # 음식점
            radius=5000,
            count=3,
            exclude_content_id=content_id,
        )

    # 5) 인기순위 정보 (MongoDB popular_spots에 있으면 순위 표시)
    popular_info = PopularSpotModel.get_popular_by_contentid(content_id)

    return render_template(
        'spots/api_detail.html',
        common=common,
        intro=intro,
        images=images,
        type_label=type_labels.get(content_type_id, '관광'),
        content_type_id=content_type_id,
        nearby_spots=nearby_spots,
        nearby_restaurants=nearby_restaurants,
        popular_info=popular_info,
    )


# ── DB 기반 관광지 상세 ─────────────────────────────────────────────────────────
@spots_bp.route('/<spot_id>')
def detail(spot_id):
    """관광지 상세 페이지 + 리뷰 목록."""
    spot = SpotModel.get_spot_by_id(spot_id)
    if not spot:
        flash('존재하지 않는 관광지입니다.', 'danger')
        return redirect(url_for('spots.list_spots'))

    reviews = ReviewModel.get_reviews_by_spot(spot_id)

    already_reviewed = False
    if 'user_id' in session:
        already_reviewed = ReviewModel.user_already_reviewed(
            spot_id, session['user_id']
        )

    return render_template('spots/detail.html',
                           spot=spot,
                           reviews=reviews,
                           already_reviewed=already_reviewed)


# ── 관리자 전용 CRUD ─────────────────────────────────────────────────────────────
@spots_bp.route('/create', methods=['GET', 'POST'])
@admin_required
def create():
    """관광지 등록 (관리자 전용)."""
    if request.method == 'POST':
        name        = request.form.get('name', '').strip()
        category    = request.form.get('category', '')
        region      = request.form.get('region', '')
        description = request.form.get('description', '').strip()
        address     = request.form.get('address', '').strip()
        image_url   = request.form.get('image_url', '').strip()

        errors = []
        if not name:
            errors.append('관광지 이름을 입력해주세요.')
        if not category:
            errors.append('카테고리를 선택해주세요.')
        if not region:
            errors.append('지역을 선택해주세요.')
        if not description:
            errors.append('설명을 입력해주세요.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('spots/create.html',
                                   categories=SpotModel.CATEGORIES,
                                   regions=SpotModel.REGIONS,
                                   form=request.form)

        spot_id = SpotModel.create_spot(
            name=name, category=category, region=region,
            description=description, address=address,
            image_url=image_url, created_by=session['user_id']
        )
        flash(f'"{name}" 관광지가 등록되었습니다.', 'success')
        return redirect(url_for('spots.detail', spot_id=spot_id))

    return render_template('spots/create.html',
                           categories=SpotModel.CATEGORIES,
                           regions=SpotModel.REGIONS)


@spots_bp.route('/<spot_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit(spot_id):
    """관광지 수정 (관리자 전용)."""
    spot = SpotModel.get_spot_by_id(spot_id)
    if not spot:
        flash('존재하지 않는 관광지입니다.', 'danger')
        return redirect(url_for('spots.list_spots'))

    if request.method == 'POST':
        data = {
            'name':        request.form.get('name', '').strip(),
            'category':    request.form.get('category', ''),
            'region':      request.form.get('region', ''),
            'description': request.form.get('description', '').strip(),
            'address':     request.form.get('address', '').strip(),
            'image_url':   request.form.get('image_url', '').strip(),
        }

        errors = []
        if not data['name']:
            errors.append('관광지 이름을 입력해주세요.')
        if not data['category']:
            errors.append('카테고리를 선택해주세요.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('spots/edit.html',
                                   spot=spot,
                                   categories=SpotModel.CATEGORIES,
                                   regions=SpotModel.REGIONS)

        SpotModel.update_spot(spot_id, data)
        flash('관광지 정보가 수정되었습니다.', 'success')
        return redirect(url_for('spots.detail', spot_id=spot_id))

    return render_template('spots/edit.html',
                           spot=spot,
                           categories=SpotModel.CATEGORIES,
                           regions=SpotModel.REGIONS)


@spots_bp.route('/<spot_id>/delete', methods=['POST'])
@admin_required
def delete(spot_id):
    """관광지 삭제 (관리자 전용)."""
    spot = SpotModel.get_spot_by_id(spot_id)
    if not spot:
        flash('존재하지 않는 관광지입니다.', 'danger')
        return redirect(url_for('spots.list_spots'))

    SpotModel.delete_spot(spot_id)
    flash(f'"{spot["name"]}" 관광지가 삭제되었습니다.', 'success')
    return redirect(url_for('spots.list_spots'))
