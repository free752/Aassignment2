from pydantic import BaseModel
from typing import List


class OrderItemRead(BaseModel):
    order_item_id: int
    book_id: int
    title: str
    quantity: int


class OrderRead(BaseModel):
    order_id: int
    status: str
    total_items: int
    items: List[OrderItemRead]


class OrderListRead(BaseModel):
    order_id: int
    status: str
    total_items: int
