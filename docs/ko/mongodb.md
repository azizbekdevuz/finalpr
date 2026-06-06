# MongoDB 설정

<p align="right">
  <strong>한국어</strong> ·
  <a href="../en/mongodb.md">English</a>
</p>

이 애플리케이션의 기본 연결 문자열은 `mongodb://localhost:27017/tourism_db` 입니다. `MONGO_URI` 환경 변수로 변경할 수 있습니다.

## 사전 준비

- MongoDB가 설치되어 실행 중이어야 합니다.
- [MongoDB Compass](https://www.mongodb.com/products/compass) 사용을 권장합니다.

## `tourism_db.zip` 으로 가져오기

프로젝트에 포함된 **`tourism_db.zip`** 과 JSON 파일로 데이터를 구성합니다.

### 1. 데이터베이스·컬렉션 생성

JSON 파일에는 **데이터베이스 이름**과 **컬렉션 이름**이 포함되어 있지 않습니다. 가져오기 전에 구조를 먼저 만듭니다.

1. Compass에서 **[+] Create database** 를 클릭합니다.
2. **Database Name:** `tourism_db`
3. **Collection Name:** JSON 파일명과 동일한 이름 중 하나를 입력하고 생성합니다.
4. 생성된 DB 옆 **[+]** 로 나머지 JSON 파일과 같은 이름의 컬렉션을 모두 만듭니다.

### 2. JSON 가져오기

각 컬렉션마다:

1. 해당 컬렉션 선택
2. **Add Data** → **Import JSON or CSV file**
3. 이름이 일치하는 JSON 파일 선택 후 **Import**

### 3. 연결 확인

`.env` 예시:

```env
MONGO_URI=mongodb://localhost:27017/tourism_db
```

앱을 실행하면 `app.py`의 인덱스 생성 로직이 필요한 인덱스를 idempotent하게 만듭니다.

## Atlas(클라우드) 사용 시

1. Atlas M0 클러스터 생성
2. 네트워크 액세스 허용(IP 화이트리스트)
3. 연결 문자열을 `MONGO_URI`에 설정

```env
MONGO_URI=mongodb+srv://USER:PASSWORD@cluster.mongodb.net/tourism_db
```

배포 관련 내용은 [배포](deployment.md)를 참고하세요.
