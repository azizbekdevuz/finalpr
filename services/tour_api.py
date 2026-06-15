"""
services/tour_api.py
한국관광공사 KorService2 API 연동 모듈
Endpoint: areaBasedSyncList2  (지역기반 관광정보 동기화 목록 조회)
           detailCommon2      (공통 정보 조회)
           detailIntro2       (소개 정보 조회)
           detailImage2       (이미지 조회)
"""
import os
from typing import Any

import requests

# ── 설정 ──────────────────────────────────────────────────────────────────────
SERVICE_KEY = os.environ.get(
    'TOUR_API_KEY'
)
BASE_URL          = 'https://apis.data.go.kr/B551011/KorService2/areaBasedSyncList2'
DETAIL_COMMON     = 'https://apis.data.go.kr/B551011/KorService2/detailCommon2'
DETAIL_INTRO      = 'https://apis.data.go.kr/B551011/KorService2/detailIntro2'
DETAIL_IMAGE      = 'https://apis.data.go.kr/B551011/KorService2/detailImage2'
LOCATION_BASED    = 'https://apis.data.go.kr/B551011/KorService2/locationBasedList2'
SEARCH_KEYWORD    = 'https://apis.data.go.kr/B551011/KorService2/searchKeyword2'

# contentTypeId 매핑
CONTENT_TYPE_MAP = {
    '관광지':    '12',
    '문화시설':  '14',
    '축제/공연': '15',
    '여행코스':  '25',
    '레포츠':    '28',
    '숙박':      '32',
    '쇼핑':      '38',
    '음식점':    '39',
}

# arrange 코드
ARRANGE_LATEST   = 'C'   # 최신순 (수정일 내림차순)
ARRANGE_POPULAR  = 'O'   # 인기순
ARRANGE_NAME_ASC = 'A'   # 이름 오름차순


def fetch_spots(
    page: int = 1,
    per_page: int = 12,
    arrange: str = ARRANGE_LATEST,
    content_type_id: str = '',
    show_flag: int = 1,
) -> dict:
    """
    공공 API에서 관광지 목록을 가져옵니다.

    Returns:
        {
            'items': [...],
            'total': int,
            'page': int,
            'per_page': int,
            'total_pages': int,
        }
    """
    params: dict[str, Any] = {
        'serviceKey': SERVICE_KEY,   # 인코딩 없이 전달 (requests가 처리)
        'numOfRows':  per_page,
        'pageNo':     page,
        'MobileOS':   'ETC',
        'MobileApp':  'GabojaGo',
        '_type':      'json',
        'showflag':   show_flag,
        'arrange':    arrange,
    }
    if content_type_id:
        params['contentTypeId'] = content_type_id

    try:
        resp = requests.get(BASE_URL, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()

        body  = data['response']['body']
        total = body.get('totalCount', 0)
        raw   = body.get('items', {})

        # items 가 없거나 빈 string일 경우 처리
        if not raw or raw == '':
            items = []
        else:
            item = raw.get('item', [])
            items = item if isinstance(item, list) else [item]

        # 필드 정규화
        normalized = []
        for it in items:
            normalized.append({
                'contentid':     it.get('contentid', ''),
                'contenttypeid': it.get('contenttypeid', ''),
                'title':         it.get('title', ''),
                'addr1':         it.get('addr1', ''),
                'addr2':         it.get('addr2', ''),
                'firstimage':    it.get('firstimage', ''),
                'firstimage2':   it.get('firstimage2', ''),
                'tel':           it.get('tel', ''),
                'mapx':          it.get('mapx', ''),
                'mapy':          it.get('mapy', ''),
                'modifiedtime':  it.get('modifiedtime', ''),
                'createdtime':   it.get('createdtime', ''),
                'lDongRegnCd':   it.get('lDongRegnCd', ''),
                'lDongSignguCd': it.get('lDongSignguCd', ''),
            })

        return {
            'spots':       normalized,
            'total':       total,
            'page':        page,
            'per_page':    per_page,
            'total_pages': max(1, (total + per_page - 1) // per_page),
        }

    except requests.exceptions.Timeout:
        return _empty_result(page, per_page, error='API 요청 시간이 초과되었습니다.')
    except Exception as e:
        return _empty_result(page, per_page, error=str(e))


def _empty_result(page, per_page, error=''):
    return {
        'spots':       [],
        'total':       0,
        'page':        page,
        'per_page':    per_page,
        'total_pages': 1,
        'error':       error,
    }


# ── 상세 페이지용 API 함수들 ─────────────────────────────────────────────────────

_BASE_PARAMS = {
    'MobileOS':  'ETC',
    'MobileApp': 'GabojaGo',
    '_type':     'json',
}


def _get_item(url, params):
    """단일 item dict 반환 (없으면 None, 오류면 None)."""
    try:
        params = {**_BASE_PARAMS, 'serviceKey': SERVICE_KEY, **params}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        body = data.get('response', {}).get('body', {})
        raw  = body.get('items', {})
        if not raw or raw == '':
            return None
        item = raw.get('item', [])
        if isinstance(item, list):
            return item[0] if item else None
        return item
    except Exception:
        return None


def fetch_detail_common(content_id: str) -> dict:
    """
    detailCommon2: 공통 정보 조회
    반환 필드: contentid, contenttypeid, title, addr1, addr2, zipcode,
               tel, telname, homepage, firstimage, firstimage2,
               mapx, mapy, overview, createdtime, modifiedtime
    """
    return _get_item(DETAIL_COMMON, {'contentId': content_id}) or {}


def fetch_detail_intro(content_id: str, content_type_id: str) -> dict:
    """
    detailIntro2: 소개 정보 조회 (contentTypeId 별 필드 다름)
    관광지(12) 주요 필드: infocenter, usetime, parking, restdate,
                          accomcount, chkbabycarriage, chkpet, chkcreditcard
    """
    return _get_item(DETAIL_INTRO, {
        'contentId':     content_id,
        'contentTypeId': content_type_id,
    }) or {}


def fetch_detail_images(content_id: str) -> list:
    """
    detailImage2: 이미지 목록 조회
    반환 필드: originimgurl, smallimageurl, imgname, cpyrhtDivCd, serialnum
    """
    try:
        params: dict[str, Any] = {
            **_BASE_PARAMS,
            'serviceKey': SERVICE_KEY,
            'contentId':  content_id,
            'imageYN':    'Y',
        }
        resp = requests.get(DETAIL_IMAGE, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        body = data.get('response', {}).get('body', {})
        raw  = body.get('items', {})
        if not raw or raw == '':
            return []
        item = raw.get('item', [])
        if not isinstance(item, list):
            item = [item]
        return item
    except Exception:
        return []


def fetch_nearby(
    mapx: str,
    mapy: str,
    content_type_id: str,
    radius: int = 5000,
    count: int = 3,
    exclude_content_id: str = '',
) -> list:
    """
    locationBasedList2: GPS 좌표 기반 거리순 관광정보 조회

    Args:
        mapx:             경도 (WGS84)
        mapy:             위도 (WGS84)
        content_type_id:  '12'=관광지, '39'=음식점 등
        radius:           반경(m), 최대 20000
        count:            반환 개수
        exclude_content_id: 제외할 contentid (현재 페이지 자신)

    Returns:
        리스트 (거리순 정렬, count개 이하)
    """
    try:
        params: dict[str, Any] = {
            **_BASE_PARAMS,
            'serviceKey':    SERVICE_KEY,
            'numOfRows':     count + 5,   # 자신 제외 후 count개 확보
            'pageNo':        1,
            'mapX':          mapx,
            'mapY':          mapy,
            'radius':        radius,
            'contentTypeId': content_type_id,
            'arrange':       'S',         # S = 거리순
        }
        resp = requests.get(LOCATION_BASED, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        body = data.get('response', {}).get('body', {})
        raw  = body.get('items', {})
        if not raw or raw == '':
            return []
        item = raw.get('item', [])
        if not isinstance(item, list):
            item = [item]

        # 자신 제외
        if exclude_content_id:
            item = [i for i in item if str(i.get('contentid', '')) != str(exclude_content_id)]

        return item[:count]
    except Exception:
        return []


def fetch_search_keyword(keyword: str, num_of_rows: int = 5) -> list:
    """
    searchKeyword2: 키워드 기반 관광정보 검색

    Args:
        keyword:      검색어 (관광지명)
        num_of_rows:  반환 최대 개수

    Returns:
        리스트 (각 항목: contentid, contenttypeid, title, addr1, firstimage, mapx, mapy 등)
    """
    try:
        params: dict[str, Any] = {
            **_BASE_PARAMS,
            'serviceKey': SERVICE_KEY,
            'numOfRows':  num_of_rows,
            'pageNo':     1,
            'keyword':    keyword,
            'arrange':    'A',   # 이름순
        }
        resp = requests.get(SEARCH_KEYWORD, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        body = data.get('response', {}).get('body', {})
        raw  = body.get('items', {})
        if not raw or raw == '':
            return []
        item = raw.get('item', [])
        if not isinstance(item, list):
            item = [item]
        return item
    except Exception:
        return []


def fetch_first_spot_by_keyword(keyword: str) -> dict:
    """
    searchKeyword2: 키워드로 관광지(contentTypeId=12) 검색 후
    생성일 기준 정렬(arrange=D) 하며 전체 페이지를 탐색하여
    contentid가 가장 작은(=가장 먼저 등록된) 관광지를 반환합니다.

    Args:
        keyword: 검색 키워드 (예: '경복궁', '부산')

    Returns:
        관광지 dict (없으면 빈 dict)
        포함 필드: contentid, title, addr1, firstimage, mapx, mapy 등
    """
    PER_PAGE = 100   # 한 번에 최대한 많이 받아 페이지 수 최소화

    all_items = []
    page      = 1

    while True:
        try:
            params: dict[str, Any] = {
                **_BASE_PARAMS,
                'serviceKey':    SERVICE_KEY,
                'numOfRows':     PER_PAGE,
                'pageNo':        page,
                'keyword':       keyword,
                'contentTypeId': '12',   # 관광지
                'arrange':       'D',    # 생성일순
            }
            resp = requests.get(SEARCH_KEYWORD, params=params, timeout=10)
            resp.raise_for_status()
            data  = resp.json()
            body  = data.get('response', {}).get('body', {})
            total = int(body.get('totalCount', 0))
            raw   = body.get('items', {})

            if not raw or raw == '':
                break

            item = raw.get('item', [])
            if not isinstance(item, list):
                item = [item]

            all_items.extend(item)

            # 모든 페이지 수집 완료 확인
            if page * PER_PAGE >= total:
                break
            page += 1

        except Exception:
            break

    if not all_items:
        return {}

    # contentid 최솟값(= 가장 먼저 등록된) 항목 선택
    try:
        best = min(all_items, key=lambda x: int(x.get('contentid', 999999999)))
        return best
    except (ValueError, TypeError):
        return all_items[0] if all_items else {}

