# Bookstore Backend (FastAPI)

## 1) 프로젝트 개요 (문제정의 / 주요 기능)
### 문제정의
도서 쇼핑몰 도메인(도서/저자/주문/즐겨찾기)을 위한 REST API 백엔드 서버를 구현합니다.  
JWT 기반 인증/인가(ROLE_USER/ROLE_ADMIN), 표준 응답 포맷, 로깅 미들웨어, Rate Limit(429) 처리를 포함합니다.

### 주요 기능 목록
- 인증: 회원가입/로그인, Access/Refresh Token 발급 및 재발급(Refresh)
- 권한: ROLE_USER / ROLE_ADMIN 접근 제어
- 도서(Books): 목록/상세 조회, (ADMIN) 생성/수정/삭제
- 저자(Authors): 목록/상세 조회, (ADMIN) 생성/수정/삭제
- 주문(Orders): (USER) 주문 생성/내 주문 조회, (ADMIN) 전체 주문 목록 조회
- 즐겨찾기(Favorites): 추가/삭제/목록
- 공통: 페이지네이션(page/size) 및 정렬(sort=field,asc|desc)
- 공통: 요청 로깅 미들웨어, 레이트리밋 미들웨어(429)

---

## 2) 실행 방법

### 로컬 실행
#### 1) 의존성 설치
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
```

#### 2) 환경변수 준비 (.env)
```bash
# Windows PowerShell
copy .env.example .env
```
- `.env`에 DB/JWT 값 설정
- `.env`는 GitHub public repo에 올리지 않고, Classroom으로 제출

#### 3) 마이그레이션 / 시드
```bash
alembic upgrade head
python seed.py
```

#### 4) 서버 실행
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

---

## 3) 환경변수 설명 (.env.example와 매칭)

| Key | Example | Description |
|---|---|---|
| DATABASE_URL | mysql+pymysql://user:pass@127.0.0.1:3306/assignment2?charset=utf8mb4 | DB 접속 URL |
| JWT_SECRET | change-me | JWT 서명 비밀키 |
| ACCESS_TOKEN_EXPIRE_MINUTES | 1 | Access Token 만료(분) |
| REFRESH_TOKEN_EXPIRE_DAYS | 7 | Refresh Token 만료(일) |
| CORS_ALLOW_ORIGINS | * | CORS 허용 Origin |
| RATE_LIMIT_MAX | 60 | 윈도우 내 허용 요청 수 |
| RATE_LIMIT_WINDOW_SEC | 60 | 레이트리밋 윈도우(초) |

---

## 4) 배포 주소 (JCloud)
- Base URL (API Root): `http://<JCLOUD_PUBLIC_IP>:<PORT>/api/v1`
- Swagger URL: `http://<JCLOUD_PUBLIC_IP>:<PORT>/docs`
- Health URL: `http://<JCLOUD_PUBLIC_IP>:<PORT>/health`

---

## 5) 인증 플로우 설명 (JWT Access/Refresh)
1. 로그인: `POST /api/v1/auth/login`
2. 응답으로 `access_token` + `refresh_token` 발급
3. 보호 API 호출 시 헤더 포함: `Authorization: Bearer <access_token>`
4. access token 만료 시: `POST /api/v1/auth/refresh`로 재발급
5. 미인증: `401`, 권한 부족: `403`

---

## 6) 역할/권한표 (ROLE_USER / ROLE_ADMIN)

| Category | API | ROLE_USER | ROLE_ADMIN |
|---|---|---:|---:|
| Auth | 회원가입/로그인/리프레시 | ✅ | ✅ |
| Books | 목록/상세 조회 | ✅ | ✅ |
| Books | 생성/수정/삭제 | ❌ | ✅ |
| Authors | 목록/상세 조회 | ✅ | ✅ |
| Authors | 생성/수정/삭제 | ❌ | ✅ |
| Favorites | 추가/삭제/목록 | ✅ | ✅ |
| Orders (User) | 주문 생성/내 주문 조회 | ✅ | ✅ |
| Orders (Admin) | 전체 주문 목록 | ❌ | ✅ |
| Users (Admin) | 유저 목록/관리 | ❌ | ✅ |

---

## 7) 예제 계정 (Seed 기준)
- USER: `user1@example.com / P@ssw0rd!`
- ADMIN: `admin@example.com / P@ssw0rd!`
  - ADMIN 계정은 도서/저자 생성 및 관리자 목록 API 테스트에 사용합니다.

> seed 계정이 다르면 `seed.py` 기준으로 수정하세요.

---

## 8) DB 연결 정보(테스트용)
> 비밀번호는 GitHub에 쓰지 않습니다(Classroom 제출용 파일에만 포함).

- Host: `<DB_HOST>`
- Port: `3306`
- Database: `assignment2`
- User: `<DB_USER>` (권한: assignment2 DB에 대한 CRUD)
- Connect:
```bash
mysql -u <DB_USER> -p -h <DB_HOST> -P 3306 assignment2
```

---

## 9) 엔드포인트 요약표 (URL · 메서드 · 설명)
> 실제 구현된 URL이 다르면 Swagger 기준으로 맞춰 주세요.

### Auth
| Method | URL | Description |
|---|---|---|
| POST | /api/v1/auth/register | 회원가입 |
| POST | /api/v1/auth/login | 로그인(토큰 발급) |
| POST | /api/v1/auth/refresh | 토큰 재발급 |

### Books
| Method | URL | Description |
|---|---|---|
| GET | /api/v1/books | 도서 목록(페이지/정렬) |
| GET | /api/v1/books/{book_id} | 도서 상세 |
| POST | /api/v1/books | 도서 생성(ADMIN) |
| PUT | /api/v1/books/{book_id} | 도서 수정(ADMIN) |
| DELETE | /api/v1/books/{book_id} | 도서 삭제(ADMIN) |

### Authors
| Method | URL | Description |
|---|---|---|
| GET | /api/v1/authors | 저자 목록(페이지/정렬) |
| GET | /api/v1/authors/{author_id} | 저자 상세 |
| POST | /api/v1/authors | 저자 생성(ADMIN) |
| PUT | /api/v1/authors/{author_id} | 저자 수정(ADMIN) |
| DELETE | /api/v1/authors/{author_id} | 저자 삭제(ADMIN) |

### Favorites
| Method | URL | Description |
|---|---|---|
| GET | /api/v1/favorites | 즐겨찾기 목록 |
| POST | /api/v1/favorites | 즐겨찾기 추가 |
| DELETE | /api/v1/favorites/{favorite_id} | 즐겨찾기 삭제 |

### Orders
| Method | URL | Description |
|---|---|---|
| POST | /api/v1/orders | 주문 생성 |
| GET | /api/v1/orders | 내 주문 목록 |
| GET | /api/v1/orders/admin | 전체 주문 목록(ADMIN) |

### Users (Admin)
| Method | URL | Description |
|---|---|---|
| GET | /api/v1/users | 유저 목록(ADMIN) |

---

## 10) 성능/보안 고려사항
- Rate Limit 미들웨어로 과도한 요청에 대해 `429 Too Many Requests` 반환
- JWT 인증으로 보호 API 접근 제한, role 기반 인가(`403`)
- 목록 API는 페이지네이션으로 대량 조회 비용 제한
- 정렬 파라미터(`sort=field,desc`) 지원

---

## 11) 한계와 개선 계획
- 테스트 코드/CI 미구현 → 추후 pytest + GitHub Actions 추가
- 캐싱/검색 최적화 미적용 → 추후 Redis 등 도입
- API 스키마/문서 자동화 고도화
