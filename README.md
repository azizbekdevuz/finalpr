# 프로젝트 실행 방법

이 프로젝트는 Flask와 MongoDB를 기반으로 동작합니다.
아래 순서대로 환경과 데이터베이스를 세팅한 후 실행해 주세요.

## 1. 가상환경 설정 및 패키지 설치

터미널을 열고 프로젝트 폴더로 이동한 후 아래 명령어를 실행합니다.

```bash
# 가상환경 생성 (최초 1회)
python -m venv venv

# 가상환경 활성화 (Windows)
.\venv\Scripts\activate

# 가상환경 활성화 (Mac/Linux)
# source venv/bin/activate

# 필수 패키지 설치
pip install -r requirements.txt
```

## 2. 데이터베이스 세팅 (중요!)

프로젝트와 함께 전달받은 **`tourism_db.zip`** 파일을 활용하여 MongoDB 데이터베이스를 세팅합니다.

1. 사전 준비
컴퓨터에 MongoDB가 설치되어 있고 실행 중이어야 합니다.

시각화 툴인 MongoDB Compass를 실행합니다.

2. 데이터베이스 및 컬렉션 생성 (가장 중요)
JSON 파일은 '데이터 내용'만 가지고 있고, '데이터베이스 이름'과 '컬렉션 이름' 정보는 포함하고 있지 않습니다. 따라서 가져오기 전에 구조를 먼저 만들어야 합니다.

MongoDB Compass 좌측 상단의 [+] (Create database) 버튼을 누릅니다.

Database Name에 아래 이름을 입력합니다.

📌 데이터베이스 이름: tourism_db

Collection Name에는 전달받은 JSON 파일 중 하나와 일치하는 이름을 먼저 하나 입력하고 [Create Database]를 누릅니다.

데이터베이스가 생성되면, 생성된 DB 이름 옆의 [+] 버튼을 누르고 나머지 JSON 파일들의 이름과 똑같이 컬렉션들을 미리 다 만들어 둡니다.

예시: users.json, products.json 파일이 있다면, Compass에 users 컬렉션과 products 컬렉션을 각각 미리 만들어 놓아야 합니다.

3. JSON 데이터 가져오기 (Import)
생성한 컬렉션마다 하나씩 데이터를 채워 넣습니다.

왼쪽 사이드바에서 데이터를 넣을 컬렉션을 선택합니다.

화면 중앙의 [Add Data] 버튼을 누르고 [Import JSON or CSV file]을 클릭합니다.

[Select File]을 눌러 해당 컬렉션 이름과 일치하는 JSON 파일을 선택합니다.

파일 형식이 JSON으로 잘 선택되었는지 확인한 후, 하단의 [Import] 버튼을 누릅니다.

나머지 컬렉션들도 똑같은 방법으로 각각의 JSON 파일을 매칭하여 데이터를 넣어줍니다.

## 3. 웹 서버 실행

기존에 가상환경(`venv`)을 활성화했던 터미널로 돌아와서 아래 명령어로 플라스크 서버를 띄웁니다.

```bash
python app.py
```

서버가 켜지면 웹 브라우저에서 `http://127.0.0.1:5000` 으로 접속하여 확인합니다.
