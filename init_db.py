
from app.db import init_db

if __name__ == "__main__":
    init_db()
    print("✅ DB 초기화 완료 (테이블 생성)")
