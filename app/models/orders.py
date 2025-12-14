from sqlalchemy import Column, BigInteger, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db import Base


class Order(Base):
    __tablename__ = "order"

    order_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False)

    status = Column(String(20), nullable=False, default="CREATED")  # CREATED, CANCELED 등
    total_items = Column(Integer, nullable=False, default=0)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_item"

    order_item_id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(BigInteger, ForeignKey("order.order_id", ondelete="CASCADE"), nullable=False)

    book_id = Column(BigInteger, ForeignKey("book.book_id", ondelete="RESTRICT"), nullable=False)
    title = Column(String(255), nullable=False)        # 주문 당시 제목 스냅샷
    quantity = Column(Integer, nullable=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    order = relationship("Order", back_populates="items")
