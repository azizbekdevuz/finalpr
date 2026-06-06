# 가보자고 (Gabojago)

<p align="right">
  <strong>한국어</strong> ·
  <a href="./README.en.md">English</a>
</p>

한국 관광 정보·리뷰·코스 추천을 제공하는 Flask 웹 애플리케이션입니다. 지역·카테고리별 관광지 검색, Tour API 연동, Google/Kakao OAuth, 한국어/영어 UI를 지원합니다.

**상세 문서:** [docs/ko/README.md](docs/ko/README.md)

## 주요 기능

- 인기 관광지·지역별 탐색 및 상세 페이지
- 사용자 리뷰 작성·필터·정렬
- Tour API 기반 코스 페이지 및 (로컬 Ollama 연동 시) AI 코스 추천
- 아이디/비밀번호 + Google·Kakao OIDC 로그인
- Flask-Babel 기반 한국어/영어 전환
- 관리자 DB 직접 관리(관리자 계정)

## 기술 스택

| 영역 | 기술 |
| --- | --- |
| 백엔드 | Flask 3, Jinja2 |
| DB | MongoDB (PyMongo) |
| 인증 | 세션 + Authlib OAuth |
| UI | MDB UI Kit, Font Awesome, 커스텀 CSS |
| i18n | Flask-Babel |
| 외부 API | 한국관광공사 Tour API, (선택) Ollama |

## 아키텍처 개요

```
app.py              # 애플리케이션 팩토리, 인덱스, 블루프린트
config.py           # 환경 설정·검증
extensions/         # MongoDB, OAuth, i18n
routes/             # HTTP 블루프린트
models/             # 데이터 접근
services/           # Tour API, LLM, 인증·마이그레이션
templates/          # SSR 템플릿·매크로
static/             # CSS, JS, 업로드
translations/       # Babel 카탈로그
```

## 빠른 시작

```bash
python -m venv venv
.\venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.example .env             # 값 편집
# MongoDB 설정 → docs/ko/mongodb.md
python app.py
```

브라우저: `http://127.0.0.1:5000`

## 환경 설정

`.env.example`을 참고해 `SECRET_KEY`, `MONGO_URI` 등을 설정합니다. OAuth·Tour API·Ollama는 선택 사항이며, 설정된 항목만 활성화됩니다.

→ [환경 변수](docs/ko/configuration.md)

## OAuth

Google·Kakao 개발자 콘솔의 리디렉션 URI와 Kakao 허용 IP를 환경에 맞게 등록하세요.

→ [OAuth 설정](docs/ko/oauth.md)

## 다국어

UI 문자열 변경 후 Babel 추출·컴파일이 필요합니다.

→ [다국어(i18n)](docs/ko/localization.md)

## 테스트

```bash
pip install -r requirements-dev.txt
ruff check .
pytest -q
```

→ [테스트·검증](docs/ko/testing.md)

## 보안

- 프로덕션에서 `DEBUG=False` 및 전용 `SECRET_KEY` 필수
- OAuth는 검증된 이메일만 계정 연결
- 로그인 시 세션 교체(세션 고정 완화), 로케일 유지
- 오픈 리디렉트 방지(`services/redirect_safety.py`)

## 배포

무료 티어(Render + Atlas) 개요는 [배포](docs/ko/deployment.md)를 참고하세요.

## 문서 목록

| 문서 | 링크 |
| --- | --- |
| 로컬 설정 | [docs/ko/setup.md](docs/ko/setup.md) |
| MongoDB | [docs/ko/mongodb.md](docs/ko/mongodb.md) |
| 환경 변수 | [docs/ko/configuration.md](docs/ko/configuration.md) |
| OAuth | [docs/ko/oauth.md](docs/ko/oauth.md) |
| i18n | [docs/ko/localization.md](docs/ko/localization.md) |
| 마이그레이션 | [docs/ko/migrations.md](docs/ko/migrations.md) |
| 테스트 | [docs/ko/testing.md](docs/ko/testing.md) |
| 배포 | [docs/ko/deployment.md](docs/ko/deployment.md) |
