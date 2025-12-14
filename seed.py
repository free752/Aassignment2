# seed.py
import random
import string
from datetime import datetime

from sqlalchemy import func
from app.db import SessionLocal
from app.core.security import get_password_hash

from app.models.users import User
from app.models.books import Author, Book, Favorite
from app.models.carts import Cart, CartItem
from app.models.orders import Order, OrderItem


def _rand_word(n=8):
    return "".join(random.choice(string.ascii_lowercase) for _ in range(n))


def ensure_admin(db):
    admin = db.query(User).filter(User.email == "admin@example.com").first()
    if admin:
        return admin

    admin = User(
        email="admin@example.com",
        password=get_password_hash("P@ssw0rd!"),
        name="Admin",
        role="admin",
        is_korean=True,
        address="Seoul",
        phone_number="01000000000",
        birth_date="2000-01-01",
        gender="M",
        profile="seed admin",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def ensure_users(db, target_users=30):
    existing = db.query(func.count(User.user_id)).scalar() or 0
    need = max(0, target_users - existing)

    for i in range(need):
        idx = existing + i + 1
        u = User(
            email=f"user{idx}@example.com",
            password=get_password_hash("P@ssw0rd!"),
            name=f"User{idx}",
            role="user",
            is_korean=True,
            address=f"Addr {_rand_word(6)}",
            phone_number=f"010{random.randint(10000000, 99999999)}",
            birth_date="2000-01-01",
            gender=random.choice(["M", "F"]),
            profile="seed user",
        )
        db.add(u)

    db.commit()


def ensure_authors(db, target_authors=50):
    existing = db.query(func.count(Author.author_id)).scalar() or 0
    need = max(0, target_authors - existing)

    for i in range(need):
        idx = existing + i + 1
        a = Author(name=f"Author {idx}", profile=f"profile {_rand_word(12)}")
        db.add(a)

    db.commit()


def ensure_books(db, target_books=200):
    author_ids = [x[0] for x in db.query(Author.author_id).all()]
    if not author_ids:
        raise RuntimeError("authors가 0개라서 book을 못 만듦. 먼저 authors seed 해야 함.")

    existing = db.query(func.count(Book.book_id)).scalar() or 0
    need = max(0, target_books - existing)

    for i in range(need):
        idx = existing + i + 1
        b = Book(
            title=f"Book {idx} {_rand_word(5)}",
            description=f"desc {_rand_word(20)}",
            price=random.randint(1000, 50000),
            stock=random.randint(1, 100),
            author_id=random.choice(author_ids),
        )
        db.add(b)

    db.commit()


def ensure_carts_and_items(db, max_items_per_user=5):
    users = db.query(User).all()
    book_ids = [x[0] for x in db.query(Book.book_id).all()]
    if not book_ids:
        return

    for u in users:
        cart = db.query(Cart).filter(Cart.user_id == u.user_id).first()
        if not cart:
            cart = Cart(user_id=u.user_id)
            db.add(cart)
            db.flush()  # cart_id 필요

        # 기존 담긴 책 조회
        existing_items = {ci.book_id for ci in db.query(CartItem).filter(CartItem.cart_id == cart.cart_id).all()}
        want = random.randint(0, max_items_per_user)
        picks = random.sample(book_ids, k=min(want, len(book_ids)))

        for bid in picks:
            if bid in existing_items:
                continue
            db.add(CartItem(cart_id=cart.cart_id, book_id=bid, quantity=random.randint(1, 3)))

    db.commit()


def ensure_favorites(db, max_fav_per_user=5):
    users = db.query(User).all()
    book_ids = [x[0] for x in db.query(Book.book_id).all()]
    if not book_ids:
        return

    for u in users:
        # Unique(user_id, book_id) 때문에 중복 방지
        existing = {
            x[0] for x in db.query(Favorite.book_id).filter(Favorite.user_id == u.user_id).all()
        }
        want = random.randint(0, max_fav_per_user)
        picks = random.sample(book_ids, k=min(want, len(book_ids)))

        for bid in picks:
            if bid in existing:
                continue
            db.add(Favorite(user_id=u.user_id, book_id=bid))

    db.commit()


def ensure_orders(db, max_orders_per_user=2, max_items_per_order=3):
    users = db.query(User).all()
    book_ids = [x[0] for x in db.query(Book.book_id).all()]
    if not book_ids:
        return

    for u in users:
        for _ in range(random.randint(0, max_orders_per_user)):
            order = Order(
                user_id=u.user_id,
                status="CREATED",
                total_items=0,
                created_at=datetime.now(),
            )
            db.add(order)
            db.flush()  # order_id 확보

            picks = random.sample(book_ids, k=min(random.randint(1, max_items_per_order), len(book_ids)))
            total_items = 0
            for bid in picks:
                qty = random.randint(1, 3)
                total_items += qty
                db.add(OrderItem(order_id=order.order_id, book_id=bid, quantity=qty))

            order.total_items = total_items

    db.commit()


def main():
    random.seed(42)
    db = SessionLocal()
    try:
        ensure_admin(db)
        ensure_users(db, target_users=30)
        ensure_authors(db, target_authors=50)
        ensure_books(db, target_books=200)
        ensure_carts_and_items(db, max_items_per_user=5)
        ensure_favorites(db, max_fav_per_user=5)
        ensure_orders(db, max_orders_per_user=2, max_items_per_order=3)

        # 대충 현재 총량 출력
        print("seed done:",
              "users=", db.query(func.count(User.user_id)).scalar(),
              "authors=", db.query(func.count(Author.author_id)).scalar(),
              "books=", db.query(func.count(Book.book_id)).scalar(),
              "favorites=", db.query(func.count(Favorite.favorite_id)).scalar(),
              "carts=", db.query(func.count(Cart.cart_id)).scalar(),
              "cart_items=", db.query(func.count(CartItem.cart_item_id)).scalar(),
              "orders=", db.query(func.count(Order.order_id)).scalar(),
              "order_items=", db.query(func.count(OrderItem.order_item_id)).scalar(),
              )
    finally:
        db.close()


if __name__ == "__main__":
    main()
