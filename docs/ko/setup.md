# 로컬 환경 설정

<p align="right">
  <strong>한국어</strong> ·
  <a href="../en/setup.md">English</a>
</p>

## 요구 사항

- Python 3.11 이상 권장
- MongoDB (로컬 또는 [MongoDB Atlas](https://www.mongodb.com/cloud/atlas))
- (선택) Ollama — AI 코스 추천 기능

## 가상환경 및 패키지

```bash
python -m venv venv

# Windows
.\venv\Scripts\activate

# macOS / Linux
# source venv/bin/activate

pip install -r requirements.txt
```

개발·검증 도구(pytest, ruff, mypy 등)가 필요하면:

```bash
pip install -r requirements-dev.txt
```

## 환경 파일

```bash
cp .env.example .env
```

변수 설명은 [환경 변수](configuration.md)를 참고하세요. `.env`는 절대 커밋하지 마세요.

## 데이터베이스

MongoDB를 준비한 뒤 [MongoDB 설정](mongodb.md)을 따라 `tourism_db`를 구성합니다.

## 실행

```bash
python app.py
```

브라우저에서 `http://127.0.0.1:5000` 으로 접속합니다.

프로덕션에서는 Flask 개발 서버 대신 Gunicorn 등 WSGI 서버를 사용하세요. 자세한 내용은 [배포](deployment.md)를 참고하세요.
