from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.core.security import get_current_user
from app.models.users import User
from app.models.books import Book
from app.models.carts import Cart, CartItem
from app.schemas.carts import CartItemCreate, CartItemUpdate, CartRead, CartItemRead, CartItemPut

router = APIRouter(prefix="/api/v1/cart", tags=["cart"])


def _get_or_create_cart(db: Session, user_id: int) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if cart:
        return cart
    cart = Cart(user_id=user_id)
    db.add(cart)
    db.commit()
    db.refresh(cart)
    return cart


@router.post("/items", status_code=status.HTTP_201_CREATED)
def add_cart_item(
    payload: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    book = db.query(Book).filter(Book.book_id == payload.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="BOOK_NOT_FOUND")

    cart = _get_or_create_cart(db, current_user.user_id)

    item = db.query(CartItem).filter(
        CartItem.cart_id == cart.cart_id,
        CartItem.book_id == payload.book_id,
    ).first()

    # 이미 있으면 수량 증가(충돌로 막고 싶으면 409로 바꿔도 됨)
    if item:
        item.quantity += payload.quantity
        db.commit()
        db.refresh(item)
        return {
            "cart_item_id": item.cart_item_id,
            "book_id": book.book_id,
            "title": book.title,
            "quantity": item.quantity,
        }

    item = CartItem(cart_id=cart.cart_id, book_id=payload.book_id, quantity=payload.quantity)
    db.add(item)
    db.commit()
    db.refresh(item)

    return {
        "cart_item_id": item.cart_item_id,
        "book_id": book.book_id,
        "title": book.title,
        "quantity": item.quantity,
    }


@router.get("", response_model=CartRead)
def get_my_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart = db.query(Cart).filter(Cart.user_id == current_user.user_id).first()
    if not cart:
        # 빈 카트 반환(스펙 취향)
        return {"cart_id": 0, "items": []}

    rows = (
        db.query(CartItem, Book)
        .join(Book, CartItem.book_id == Book.book_id)
        .filter(CartItem.cart_id == cart.cart_id)
        .order_by(CartItem.cart_item_id.desc())
        .all()
    )

    items = [
        CartItemRead(
            cart_item_id=item.cart_item_id,
            book_id=book.book_id,
            title=book.title,
            quantity=item.quantity,
        )
        for item, book in rows
    ]
    return {"cart_id": cart.cart_id, "items": items}


@router.patch("/items/{cart_item_id}")
def update_cart_item(
    cart_item_id: int,
    payload: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart = db.query(Cart).filter(Cart.user_id == current_user.user_id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="CART_NOT_FOUND")

    item = db.query(CartItem).filter(
        CartItem.cart_item_id == cart_item_id,
        CartItem.cart_id == cart.cart_id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="CART_ITEM_NOT_FOUND")

    item.quantity = payload.quantity
    db.commit()
    db.refresh(item)

    book = db.query(Book).filter(Book.book_id == item.book_id).first()
    return {
        "cart_item_id": item.cart_item_id,
        "book_id": item.book_id,
        "title": book.title if book else "",
        "quantity": item.quantity,
    }


@router.delete("/items/{cart_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cart_item(
    cart_item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart = db.query(Cart).filter(Cart.user_id == current_user.user_id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="CART_NOT_FOUND")

    item = db.query(CartItem).filter(
        CartItem.cart_item_id == cart_item_id,
        CartItem.cart_id == cart.cart_id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="CART_ITEM_NOT_FOUND")

    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.put("/items/{item_id}")
def put_cart_item_quantity(
    item_id: int,
    body: CartItemPut,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    item = (
        db.query(CartItem)
        .filter(CartItem.cart_item_id == item_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="CART_ITEM_NOT_FOUND")

    # 🔥 소유자 체크(모델에 user_id / cart.user_id 구조에 맞게 하나만 적용)
    # 예시1) CartItem에 user_id가 있는 경우
    if getattr(item, "user_id", None) is not None and item.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="FORBIDDEN")

    item.quantity = body.quantity
    db.commit()
    db.refresh(item)

    return {"isSuccess": True, "message": "OK", "payload": {"cart_item_id": item.cart_item_id, "quantity": item.quantity}}