"""
Korea Tourism Organization KorService2 client.
/ 한국관광공사 KorService2 API 연동 모듈.
"""
import os
from typing import Any

import requests

SERVICE_KEY = os.environ.get(
    'TOUR_API_KEY'
)
BASE_URL          = 'https://apis.data.go.kr/B551011/KorService2/areaBasedSyncList2'
DETAIL_COMMON     = 'https://apis.data.go.kr/B551011/KorService2/detailCommon2'
DETAIL_INTRO      = 'https://apis.data.go.kr/B551011/KorService2/detailIntro2'
DETAIL_IMAGE      = 'https://apis.data.go.kr/B551011/KorService2/detailImage2'
LOCATION_BASED    = 'https://apis.data.go.kr/B551011/KorService2/locationBasedList2'
SEARCH_KEYWORD    = 'https://apis.data.go.kr/B551011/KorService2/searchKeyword2'

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

ARRANGE_LATEST   = 'C'
ARRANGE_POPULAR  = 'O'
ARRANGE_NAME_ASC = 'A'


def fetch_spots(
    page: int = 1,
    per_page: int = 12,
    arrange: str = ARRANGE_LATEST,
    content_type_id: str = '',
    show_flag: int = 1,
) -> dict:
    """
    Fetch paginated spots from the public tourism API.

    Returns:
        dict with keys: spots, total, page, per_page, total_pages
    """
    params: dict[str, Any] = {
        # Pass key raw; requests encodes it. / 키는 인코딩 없이 전달(requests가 처리).
        'serviceKey': SERVICE_KEY,
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

        if not raw or raw == '':
            items = []
        else:
            item = raw.get('item', [])
            items = item if isinstance(item, list) else [item]

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


_BASE_PARAMS = {
    'MobileOS':  'ETC',
    'MobileApp': 'GabojaGo',
    '_type':     'json',
}


def _get_item(url, params):
    """Return a single API item dict, or None on miss/error."""
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
    """Fetch detailCommon2 fields for a content ID."""
    return _get_item(DETAIL_COMMON, {'contentId': content_id}) or {}


def fetch_detail_intro(content_id: str, content_type_id: str) -> dict:
    """Fetch detailIntro2 fields (shape varies by contentTypeId)."""
    return _get_item(DETAIL_INTRO, {
        'contentId':     content_id,
        'contentTypeId': content_type_id,
    }) or {}


def fetch_detail_images(content_id: str) -> list:
    """Fetch detailImage2 image list for a content ID."""
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
    """Fetch GPS-nearby spots sorted by distance (locationBasedList2)."""
    try:
        params: dict[str, Any] = {
            **_BASE_PARAMS,
            'serviceKey':    SERVICE_KEY,
            # Request extra rows so exclusion still yields `count`. / 제외 후에도 count개를 확보합니다.
            'numOfRows':     count + 5,
            'pageNo':        1,
            'mapX':          mapx,
            'mapY':          mapy,
            'radius':        radius,
            'contentTypeId': content_type_id,
            'arrange':       'S',
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

        if exclude_content_id:
            item = [i for i in item if str(i.get('contentid', '')) != str(exclude_content_id)]

        return item[:count]
    except Exception:
        return []


def fetch_search_keyword(keyword: str, num_of_rows: int = 5) -> list:
    """Search spots by keyword (searchKeyword2)."""
    try:
        params: dict[str, Any] = {
            **_BASE_PARAMS,
            'serviceKey': SERVICE_KEY,
            'numOfRows':  num_of_rows,
            'pageNo':     1,
            'keyword':    keyword,
            'arrange':    'A',
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
    """Return the oldest registered attraction match for a keyword (min contentid)."""
    PER_PAGE = 100

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
                'contentTypeId': '12',
                'arrange':       'D',
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

            if page * PER_PAGE >= total:
                break
            page += 1

        except Exception:
            break

    if not all_items:
        return {}

    # Lowest contentid = earliest registration. / 최소 contentid가 가장 먼저 등록된 항목입니다.
    try:
        best = min(all_items, key=lambda x: int(x.get('contentid', 999999999)))
        return best
    except (ValueError, TypeError):
        return all_items[0] if all_items else {}

