# 다국어(i18n)

<p align="right">
  <strong>한국어</strong> ·
  <a href="../en/localization.md">English</a>
</p>

[Flask-Babel](https://python-babel.github.io/flask-babel/)로 한국어(`ko`)·영어(`en`)를 지원합니다.

## 동작

- 기본 로케일: `ko`
- 우선순위: 세션 → `Accept-Language` → 기본값
- 네비게이션 언어 전환 또는 `POST /language/<locale>`

번역 파일: `translations/<locale>/LC_MESSAGES/messages.po`

## 문자열 변경 후

```bash
pybabel extract -F babel.cfg -o messages.pot .
pybabel update -i messages.pot -d translations
# messages.po 편집 후
pybabel compile -d translations
```

`babel.cfg`는 추출 대상(`templates/`, `routes/` 등)을 정의합니다.

## 템플릿·코드

- Jinja: `{{ _('...') }}`
- Python: `from flask_babel import gettext as _` 후 `_('...')`
- 사용자에게 보이는 새 문자열 추가 시 위 워크플로로 카탈로그를 갱신하세요.

## 주의

- 지역명·관광 데이터 등 **콘텐츠 데이터**는 API/DB 값일 수 있으며 UI 설명문만 번역 대상입니다.
- `REGION_META` 등 앱 소유 UI 문구는 요청 시점 로케일로 해석됩니다.
