# 데이터 마이그레이션

<p align="right">
  <strong>한국어</strong> ·
  <a href="../en/migrations.md">English</a>
</p>

## 이메일 정규화 백필

신규·갱신 사용자는 `email_normalized` 필드를 저장합니다. 레거시 문서와의 호환 조회는 유지됩니다.

### 드라이 런(기본)

```bash
flask --app app:create_app backfill-emails
```

변경 예정 항목과 충돌만 보고하며 **쓰기는 하지 않습니다**.

### 적용

```bash
flask --app app:create_app backfill-emails --apply
```

멱등(idempotent)이며 계정을 삭제·병합하지 않습니다.

### 인덱스

드라이 런에서 충돌이 없음을 확인한 뒤에만 `email_normalized` 유니크 인덱스 추가를 검토하세요. 앱 기동 시 생성되는 인덱스와 백필 명령은 `services/migrations.py`에 정의되어 있습니다.

## 일반 원칙

- 운영 DB에 대해 **비파괴** 마이그레이션만 사용합니다.
- 백업 없이 강제 스키마 변경을 하지 마세요.
