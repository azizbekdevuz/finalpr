"""
seed.py — 초기 샘플 데이터 삽입 스크립트
실행: python seed.py
"""

import os
import json
from bson import ObjectId
from app import create_app
from extensions.db import mongo
from models.user import create_user
from models.spot import create_spot

# popular_spots JSON 경로 (seed.py 와 같은 폴더에 있으면 자동 인식)
_BASE = os.path.dirname(os.path.abspath(__file__))
_POPULAR_SPOTS_PATH = os.path.join(_BASE, 'tourism_db.popular_spots.json')

SAMPLE_SPOTS = [
    {
        'name': '경복궁',
        'category': '문화/역사',
        'region': '서울',
        'description': '조선시대 최고의 법궁으로, 조선 왕조의 정궁입니다. '
                       '웅장한 근정전과 아름다운 경회루가 인상적이며 '
                       '매일 수문장 교대식이 펼쳐집니다.',
        'address': '서울특별시 종로구 사직로 161',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Gyeongbokgung-GeunJeongJeon.jpg/1280px-Gyeongbokgung-GeunJeongJeon.jpg',
    },
    {
        'name': '제주 성산일출봉',
        'category': '자연',
        'region': '제주',
        'description': '제주도 동쪽 끝에 위치한 수성화산으로 유네스코 세계자연유산입니다. '
                       '정상에서 바라보는 일출이 장관을 이루며 '
                       '사방으로 펼쳐지는 바다 전경이 압도적입니다.',
        'address': '제주특별자치도 서귀포시 성산읍 일출로 284-12',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/Seongsan_Ilchulbong.jpg/1280px-Seongsan_Ilchulbong.jpg',
    },
    {
        'name': '해운대 해수욕장',
        'category': '자연',
        'region': '부산',
        'description': '대한민국에서 가장 유명한 해수욕장 중 하나로 '
                       '백사장 길이만 1.5km에 달합니다. '
                       '여름에는 수백만 명의 관광객이 방문하며 '
                       '주변에 다양한 맛집과 볼거리가 가득합니다.',
        'address': '부산광역시 해운대구 해운대해변로 264',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/84/Haeundae_beach_Busan.jpg/1280px-Haeundae_beach_Busan.jpg',
    },
    {
        'name': '불국사',
        'category': '문화/역사',
        'region': '경주',
        'description': '신라 시대에 건립된 천년 고찰로 유네스코 세계문화유산입니다. '
                       '다보탑과 석가탑이 대표적이며 '
                       '봄가을에는 특히 아름다운 풍경을 자랑합니다.',
        'address': '경상북도 경주시 불국로 385',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Bulguksa_temple_hdr.jpg/1280px-Bulguksa_temple_hdr.jpg',
    },
    {
        'name': '전주 한옥마을',
        'category': '문화/역사',
        'region': '전주',
        'description': '700여 채의 전통 한옥이 모여 있는 국내 최대 규모의 한옥 군락지입니다. '
                       '전통 문화 체험과 함께 전주비빔밥, 콩나물국밥 등 '
                       '다양한 전통 음식을 즐길 수 있습니다.',
        'address': '전라북도 전주시 완산구 기린대로 99',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/JeonjuHanokVillage.jpg/1280px-JeonjuHanokVillage.jpg',
    },
    {
        'name': '남이섬',
        'category': '자연',
        'region': '강원',
        'description': '북한강 한가운데 위치한 섬으로 드라마 "겨울연가" 촬영지로 유명합니다. '
                       '메타세쿼이아 나무길이 아름답고 '
                       '계절마다 다른 매력을 선사하는 낭만적인 여행지입니다.',
        'address': '강원도 춘천시 남산면 남이섬길 1',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Nami_Island_20200919.jpg/1280px-Nami_Island_20200919.jpg',
    },
    {
        'name': '광장시장',
        'category': '음식/맛집',
        'region': '서울',
        'description': '서울 종로구에 위치한 100년 역사의 전통시장입니다. '
                       '빈대떡, 마약김밥, 순대 등 다양한 길거리 음식이 유명하며 '
                       '직물과 의류를 비롯한 다양한 상품도 만날 수 있습니다.',
        'address': '서울특별시 종로구 창경궁로 88',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/28/Gwangjang_Market_2017.jpg/1280px-Gwangjang_Market_2017.jpg',
    },
    {
        'name': '설악산 국립공원',
        'category': '자연',
        'region': '강원',
        'description': '대한민국을 대표하는 국립공원으로 울산바위, 공룡능선, 대청봉이 유명합니다. '
                       '가을 단풍과 겨울 설경이 특히 아름다우며 '
                       '다양한 등산 코스를 즐길 수 있습니다.',
        'address': '강원도 속초시 설악산로 833',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c7/Seoraksan_in_autumn.jpg/1280px-Seoraksan_in_autumn.jpg',
    },
    {
        'name': '부산 감천문화마을',
        'category': '문화/역사',
        'region': '부산',
        'description': '한국의 산토리니라 불리는 아름다운 마을로 '
                       '알록달록한 집들이 산비탈을 가득 채우고 있습니다. '
                       '다양한 벽화와 예술 작품이 골목 곳곳에 펼쳐져 있습니다.',
        'address': '부산광역시 사하구 감내2로 203',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a3/Gamcheon_Culture_Village%2C_Busan.jpg/1280px-Gamcheon_Culture_Village%2C_Busan.jpg',
    },
    {
        'name': '제주 협재해수욕장',
        'category': '자연',
        'region': '제주',
        'description': '에메랄드빛 바다와 새하얀 모래사장이 아름다운 해수욕장입니다. '
                       '앞바다의 비양도 풍경이 인상적이며 '
                       '주변의 한림공원과 함께 방문하기 좋습니다.',
        'address': '제주특별자치도 제주시 한림읍 협재리 2497-1',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/Hyeopjaehaebyeon.jpg/1280px-Hyeopjaehaebyeon.jpg',
    },
    {
        'name': '동대문 디자인 플라자 (DDP)',
        'category': '액티비티',
        'region': '서울',
        'description': '자하 하디드가 설계한 비정형 건축물로 서울의 랜드마크입니다. '
                       '상설·특별 전시와 패션쇼 등 다양한 문화 행사가 열리며 '
                       '야경이 특히 아름다운 곳입니다.',
        'address': '서울특별시 중구 을지로 281',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9d/DDP.jpg/1280px-DDP.jpg',
    },
    {
        'name': '인사동',
        'category': '쇼핑',
        'region': '서울',
        'description': '전통 공예품, 골동품, 미술 작품을 파는 상점들이 모여 있는 거리입니다. '
                       '전통차 카페와 갤러리도 많아 문화적인 분위기를 느낄 수 있으며 '
                       '한국적인 기념품을 구입하기에 최적의 장소입니다.',
        'address': '서울특별시 종로구 인사동길',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b3/Insadong_street_in_Seoul.jpg/1280px-Insadong_street_in_Seoul.jpg',
    },
]


SAMPLE_REVIEWS = [
    {'spot_name': '경복궁',          'username': '참나물하늘소', 'rating': 5, 'content': '단순한 공원이 아니라, 전쟁과 평화에 대한 깊은 메시지를 주는 의미 있는 장소였습니다.'},
    {'spot_name': '산방산유채꽃밭',   'username': '올려다본그림', 'rating': 4, 'content': '산방산을 배경으로 찍어도 예쁜데 유채꽃까지 있으면 너무 예쁘지요. 산방산 온천도 꼭 가보세요.'},
    {'spot_name': '선암사',           'username': '폭발집중효과', 'rating': 5, 'content': '친구들과 함께 순천 선암사에 다녀왔어요. 유네스코 세계유산인 고찰인데다가 만개한 벚꽃까지 봄을 제대로 즐기고 왔습니다.'},
    {'spot_name': '레고랜드 코리아',  'username': '항공로케트',   'rating': 5, 'content': '아이가 좋아해서 왔는데 온가족이 너무 즐거워요^^ 특히 레고호텔은 아이가 더 만족하고요!!'},
    {'spot_name': '설악산 국립공원',  'username': '문암산',       'rating': 5, 'content': '사계절 다 가도 좋은 설악산 또 가보고 싶어요.'},
    {'spot_name': '올림픽공원',       'username': '동그랭이',     'rating': 5, 'content': '올림픽공원은 너무 넓어서 한바퀴 다돌기도 힘들어요. 사계절을 느낄수 있는곳이라 좋아요.'},
    {'spot_name': '해운대 해수욕장',  'username': '개인플레이',   'rating': 4, 'content': '규모가 크고 주변 놀이 시설이 많아 하루 놀기 좋습니다^^'},
]


def seed():
    app = create_app()
    with app.app_context():
        # MongoDB 연결 테스트
        try:
            mongo.db.command('ping')
        except Exception as e:
            raise RuntimeError(
                'MongoDB 서버에 연결할 수 없습니다. 로컬 MongoDB가 실행 중인지 확인하고, ' \
                'MONGO_URI 환경 변수가 올바른지 확인하세요.'
            ) from e

        # ── 기존 데이터 초기화 ──────────────────────────────────────────
        mongo.db.users.drop()
        mongo.db.tourist_spots.drop()
        mongo.db.reviews.drop()
        mongo.db.popular_spots.drop()

        # 인덱스 재생성
        mongo.db.users.create_index('username', unique=True)
        mongo.db.users.create_index('email', unique=True)

        print('기존 데이터를 초기화했습니다.')

        # ── 관리자 계정 생성 ────────────────────────────────────────────
        admin_id = create_user(
            username='admin',
            email='admin@tourism.kr',
            password='admin1234',
            role='admin'
        )
        print(f'관리자 계정 생성: admin / admin1234  (id={admin_id})')

        # ── 일반 사용자 계정 생성 ───────────────────────────────────────
        user_id = create_user(
            username='traveler',
            email='traveler@example.com',
            password='travel1234',
            role='user'
        )
        print(f'일반 사용자 계정 생성: traveler / travel1234  (id={user_id})')

        # ── 관광지 데이터 삽입 ──────────────────────────────────────────
        for s in SAMPLE_SPOTS:
            spot_id = create_spot(
                name=s['name'],
                category=s['category'],
                region=s['region'],
                description=s['description'],
                address=s['address'],
                image_url=s['image_url'],
                created_by=admin_id
            )
            print(f'  관광지 등록: {s["name"]}  (id={spot_id})')

        # ── 인기 관광지 데이터 삽입 (popular_spots) ────────────────────
        if os.path.exists(_POPULAR_SPOTS_PATH):
            with open(_POPULAR_SPOTS_PATH, encoding='utf-8') as f:
                popular_raw = json.load(f)
            for d in popular_raw:
                if isinstance(d.get('_id'), dict) and '$oid' in d['_id']:
                    d['_id'] = ObjectId(d['_id']['$oid'])
            mongo.db.popular_spots.insert_many(popular_raw)
            print(f'  인기 관광지 등록: {len(popular_raw)}개')
        else:
            print(f'  ⚠️  popular_spots JSON 파일을 찾을 수 없습니다: {_POPULAR_SPOTS_PATH}')
            print(f'     tourism_db.popular_spots.json 을 프로젝트 루트에 복사해주세요.')

        # ── 리뷰 데이터 삽입 ──────────────────────────────────────────
        from datetime import datetime, timezone
        # from bson import ObjectId
        for rv in SAMPLE_REVIEWS:
            mongo.db.reviews.insert_one({
                'spot_id':    None,
                'spot_name':  rv['spot_name'],
                'user_id':    ObjectId(admin_id),
                'username':   rv['username'],
                'rating':     rv['rating'],
                'content':    rv['content'],
                'created_at': datetime.now(timezone.utc),
            })
        print(f'  리뷰 등록: {len(SAMPLE_REVIEWS)}개')

        print('\n[완료] 시드 데이터 삽입 완료!')
        print('   - 관리자: admin / admin1234')
        print('   - 일반 사용자: traveler / travel1234')
        print(f'   - 관광지: {len(SAMPLE_SPOTS)}개')
        print(f'   - 리뷰: {len(SAMPLE_REVIEWS)}개')
        print(f'   - 인기 관광지: popular_spots JSON 참조')


if __name__ == '__main__':
    try:
        seed()
    except Exception as e:
        print('ERROR:', e)
        import traceback
        traceback.print_exc()
        print('\nMongoDB가 실행 중인지, 또는 MONGO_URI가 올바른지 확인하세요.')
