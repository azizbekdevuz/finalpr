# 배포

<p align="right">
  <strong>한국어</strong> ·
  <a href="../en/deployment.md">English</a>
</p>

## 프로덕션 체크리스트

| 항목 | 권장 값 |
| --- | --- |
| `DEBUG` | `False` |
| `SECRET_KEY` | 강한 무작위 문자열 |
| `SESSION_COOKIE_SECURE` | `True` |
| `PREFERRED_URL_SCHEME` | `https` |
| WSGI | Gunicorn 등 (개발 서버 사용 금지) |
| DB | MongoDB Atlas 등 관리형 MongoDB |

## 무료 티어 예시

| 구성 요소 | 서비스 |
| --- | --- |
| 앱 호스팅 | [Render](https://render.com) 무료 Web Service |
| 데이터베이스 | [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) M0 |
| 도메인 | `*.onrender.com` 서브도메인 |

### WSGI 진입점 예시

`wsgi.py`:

```python
from app import create_app
app = create_app()
```

시작 명령:

```bash
gunicorn --bind 0.0.0.0:$PORT --workers 2 wsgi:app
```

`requirements.txt`에 `gunicorn`을 추가하세요.

## 제한 사항

- **Ollama**는 대부분의 무료 PaaS에서 실행할 수 없습니다. AI 코스 기능은 오프라인으로 표시될 수 있습니다.
- `static/uploads`는 ephemeral 디스크일 수 있어 재배포 시 업로드가 사라질 수 있습니다.
- OAuth 콘솔에 프로덕션 콜백 URL과 Kakao 허용 IP를 등록해야 합니다.

자세한 환경 변수는 [환경 변수](configuration.md), OAuth는 [OAuth 설정](oauth.md)을 참고하세요.
