# Assignment2 - FastAPI (MySQL)

FastAPI + SQLAlchemy(MySQL)로 간단한 온라인 서점 API를 구현한 과제입니다.  
Swagger UI(`/docs`)로 테스트 가능하며, 요청 로깅 미들웨어와 다양한 HTTP 상태 코드(2xx/4xx/5xx)를 포함합니다.

## Tech Stack
- Python / FastAPI
- SQLAlchemy + PyMySQL
- MySQL
- Alembic (migrations)
- JWT Auth

---

## Requirements 체크
- [x] HTTP 메소드별 API 구현 (POST/GET/PUT/DELETE)
- [x] 각 메소드 2개씩(총 8개) 이상 구현
- [x] 요청 로깅 미들웨어 적용
- [x] 2xx / 4xx / 5xx 상태코드 다양성 확보
- [x] Swagger 테스트 및 실행 캡처 가능

---

## 대표 8개 엔드포인트 (과제 요구 충족용)
아래 8개는 “POST/GET/PUT/DELETE 각각 2개”를 맞춰서 보여주기 좋은 조합입니다.  
(전체 목록/스키마는 `/docs` 참고)

### POST (2)
- `POST /api/v1/users` : 회원 생성(회원가입)
- `POST /api/v1/cart/items` : 장바구니 아이템 추가

### GET (2)
- `GET /api/v1/books` : 도서 목록 조회
- `GET /api/v1/orders` : 내 주문 목록 조회

### PUT (2)
- `PUT /api/v1/books/{book_id}` : 도서 정보 수정
- `PUT /api/v1/cart/items/{cart_item_id}` : 장바구니 수량 수정

### DELETE (2)
- `DELETE /api/v1/orders/{order_id}` : 주문 취소
- `DELETE /api/v1/favorites/{book_id}` : 즐겨찾기 삭제

---

## 응답/에러 형태
- 정상 응답은 JSON을 반환하며(세부 스키마는 Swagger 참고),
- 에러는 보통 `{"detail": "ERROR_CODE"}` 형태로 반환됩니다.

자주 쓰는 에러 코드 예시:
- `ORDER_NOT_FOUND`
- `ALREADY_CANCELED`
- `NOT_CANCEL_REQUESTED`
- `BOOK_NOT_FOUND`
- `DB_UNAVAILABLE`

---

## 실행 방법 (로컬)

### 1) 가상환경 + 패키지 설치
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
### 2) MySQL 준비 + 환경변수(.env)

1) MySQL에 `assignment2` 데이터베이스를 생성합니다.

```sql
CREATE DATABASE assignment2 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2) 프로젝트 루트(= `alembic.ini` 파일이 있는 위치)에 `.env` 파일을 만들고 아래처럼 설정합니다.

```env
DATABASE_URL=mysql+pymysql://<user>:<password>@127.0.0.1:3306/assignment2?charset=utf8mb4
JWT_SECRET=<your-secret>
```

- `<user>` / `<password>` 는 본인 MySQL 계정으로 변경
- DB 이름이 다르면 `assignment2` 부분도 본인 DB명으로 변경

---

### 3) 마이그레이션 적용

```bash
alembic upgrade head
```

(선택) 마이그레이션 적용 여부 확인:

```bash
alembic current
alembic history --verbose
```

---

### 4) 서버 실행

```bash
uvicorn app.main:app --reload --port 8000
```

- Swagger UI: `http://127.0.0.1:8000/docs`

---

## 테스트 방법 (Swagger)

1. `/docs` 접속
2. 로그인으로 토큰 발급 (프로젝트의 로그인 API 사용)
3. Swagger 우측 상단 **Authorize**에 `Bearer <token>` 입력
4. 엔드포인트 Execute 실행 후 결과 캡처

---

## 5xx(500/503) 테스트

- 재현 가능한 방식으로 5xx를 캡처하기 위해 테스트용 엔드포인트(또는 Health Check)를 사용합니다.

예시:
- `GET /api/v1/health` : DB ping 실패 시 `503 (DB_UNAVAILABLE)`
- 테스트용 에러 엔드포인트가 있다면 `/docs`에서 500/503 재현 후 캡처

---

## 랜덤 데이터(200개 이상) 검증 (MySQL Workbench)

아래 쿼리 결과의 `total_cnt`가 200 이상이면 확인 완료:

```sql
SELECT
  (SELECT COUNT(*) FROM book) +
  (SELECT COUNT(*) FROM authors) +
  (SELECT COUNT(*) FROM user) AS total_cnt;
```

---

## 제출용 캡처 추천

- 서버 실행 터미널(uvicorn 실행 로그)
- Swagger에서 대표 8개 엔드포인트 각각 1장씩(요청/응답 보이게)
- 4xx 예시 1~2장(예: NOT_FOUND / CONFLICT)
- 5xx 예시 2장(500, 503)
- 랜덤 데이터 200+ 검증 쿼리 결과(`total_cnt`)
