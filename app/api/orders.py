from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.db import get_db
from app.core.security import get_current_user
from app.models.users import User
from app.models.books import Book
from app.models.carts import Cart, CartItem
from app.models.orders import Order, OrderItem
from app.schemas.orders import OrderRead, OrderListRead, OrderItemRead

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])
def require_admin(current_user = Depends(get_current_user)):
    if getattr(current_user, "role", None) != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    return current_user

@router.post("", status_code=status.HTTP_201_CREATED, response_model=OrderRead)
def create_order_from_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart = db.query(Cart).filter(Cart.user_id == current_user.user_id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="CART_NOT_FOUND")

    cart_items = db.query(CartItem).filter(CartItem.cart_id == cart.cart_id).all()
    if not cart_items:
        raise HTTPException(status_code=400, detail="CART_EMPTY")

    # 주문 생성
    order = Order(user_id=current_user.user_id, status="CREATED", total_items=sum(i.quantity for i in cart_items))
    db.add(order)
    db.commit()
    db.refresh(order)

    # 주문 아이템 생성(스냅샷)
    items_out = []
    for ci in cart_items:
        book = db.query(Book).filter(Book.book_id == ci.book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="BOOK_NOT_FOUND")

        oi = OrderItem(
            order_id=order.order_id,
            book_id=book.book_id,
            title=book.title,
            quantity=ci.quantity,
        )
        db.add(oi)
        db.commit()
        db.refresh(oi)

        items_out.append(OrderItemRead(
            order_item_id=oi.order_item_id,
            book_id=oi.book_id,
            title=oi.title,
            quantity=oi.quantity,
        ))

    # 카트 비우기
    for ci in cart_items:
        db.delete(ci)
    db.commit()

    return OrderRead(
        order_id=order.order_id,
        status=order.status,
        total_items=order.total_items,
        items=items_out,
    )


@router.get("", status_code=status.HTTP_200_OK)
def list_my_orders(
    include_canceled: bool = Query(False),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = (
        db.query(Order)
        .filter(Order.user_id == current_user.user_id)
        .order_by(Order.order_id.desc())
    )

    if not include_canceled:
        q = q.filter(Order.status != "CANCELED")

    orders = (
        db.query(Order)
        .filter(
            Order.user_id == current_user.user_id,
            Order.deleted_at.is_(None),
        )
        .order_by(Order.order_id.desc())
        .all()
    )

    # 너가 이미 쓰던 응답 형태 유지
    return [
        {"order_id": o.order_id, "status": o.status, "total_items": o.total_items}
        for o in orders
    ]

@router.get("/{order_id}", response_model=OrderRead)
def get_order_detail(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(
        Order.order_id == order_id,
        Order.user_id == current_user.user_id,
        Order.deleted_at.is_(None),
    ).first()
    if not order:
        raise HTTPException(404, "ORDER_NOT_FOUND")

    order_items = db.query(OrderItem).filter(OrderItem.order_id == order.order_id).all()
    items_out = [
        OrderItemRead(
            order_item_id=oi.order_item_id,
            book_id=oi.book_id,
            title=oi.title,
            quantity=oi.quantity,
        )
        for oi in order_items
    ]
    return OrderRead(order_id=order.order_id, status=order.status, total_items=order.total_items, items=items_out)


# 2) 유저 취소: DELETE지만 "삭제"가 아니라 "취소 요청"으로만 처리
@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    order = (
        db.query(Order)
        .filter(Order.order_id == order_id, Order.user_id == current_user.user_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="ORDER_NOT_FOUND")

    if order.status == "CANCELED":
        raise HTTPException(status_code=409, detail="ALREADY_CANCELED")
    if order.status == "CANCEL_REQUESTED":
        raise HTTPException(status_code=409, detail="ALREADY_REQUESTED")

    # 여기서 바로 CANCELED로 만들지 말고 "요청"으로만
    order.status = "CANCEL_REQUESTED"
    db.commit()
    return  # 204

# 3) 관리자 승인: CANCEL_REQUESTED -> CANCELED
@router.patch("/{order_id}/cancel-approve", status_code=status.HTTP_200_OK)
def approve_cancel(
    order_id: int,
    db: Session = Depends(get_db),
    admin_user=Depends(require_admin),
):
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="ORDER_NOT_FOUND")

    if order.status == "CANCELED":
        raise HTTPException(status_code=409, detail="ALREADY_CANCELED")
    if order.status != "CANCEL_REQUESTED":
        raise HTTPException(status_code=409, detail="NOT_CANCEL_REQUESTED")

    order.status = "CANCELLED"
    order.deleted_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "order_id": order.order_id,
        "status": order.status,
        "message": "CANCEL_APPROVED",
    }

# (선택) 관리자 주문 전체 조회 (원하면 Swagger 테스트 편해짐)
@router.get("/admin", status_code=status.HTTP_200_OK)
def admin_list_orders(
    status_filter: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    admin_user=Depends(require_admin),
):
    q = db.query(Order).order_by(Order.order_id.desc())
    if status_filter:
        q = q.filter(Order.status == status_filter)
    orders = q.all()
    return [
        {
            "order_id": o.order_id,
            "user_id": o.user_id,
            "status": o.status,
            "total_items": o.total_items,
        }
        for o in orders
    ]