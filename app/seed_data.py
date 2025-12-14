# seed_data.py
import os, sys, random

# app import 되게 경로 보정 (루트에서 실행 기준)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from app.db import SessionLocal
from app.models.books import Author, Book
from app.models.users import User
from app.core.security import hash_password

def main():
    db = SessionLocal()
    try:
        # 1) Authors 50명
        target_authors = 50
        cur_authors = db.query(Author).count()
        if cur_authors < target_authors:
            for i in range(cur_authors + 1, target_authors + 1):
                db.add(Author(name=f"Author {i}", profile=f"profile {i}"))
            db.commit()

        author_ids = [row[0] for row in db.query(Author.author_id).all()]

        # 2) Books 200권
        target_books = 200
        cur_books = db.query(Book).count()
        if cur_books < target_books:
            for i in range(cur_books + 1, target_books + 1):
                db.add(
                    Book(
                        title=f"Book {i}",
                        description=f"Description {i}",
                        price=random.randint(1000, 50000),
                        stock=random.randint(0, 100),
                        author_id=random.choice(author_ids),
                        status="ACTIVE",
                    )
                )
            db.commit()

        # 3) Users 20명 + admin 1명
        if not db.query(User).filter(User.email == "admin@example.com").first():
            db.add(
                User(
                    email="admin@example.com",
                    password_hash=hash_password("admin1234"),
                    name="Admin",
                    role="admin",
                )
            )
            db.commit()

        target_users = 20
        # admin 포함 count라서, 부족하면 user 계정 추가로 채움
        while db.query(User).count() < target_users:
            i = db.query(User).count() + 1
            email = f"user{i}@example.com"
            if db.query(User).filter(User.email == email).first():
                continue
            db.add(
                User(
                    email=email,
                    password_hash=hash_password("password1234"),
                    name=f"User{i}",
                    role="user",
                )
            )
            db.commit()

        print("DONE")
        print("authors =", db.query(Author).count())
        print("books   =", db.query(Book).count())
        print("users   =", db.query(User).count())

    finally:
        db.close()

if __name__ == "__main__":
    main()
