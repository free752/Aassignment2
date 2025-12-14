from pydantic import BaseModel, Field
from typing import List


class CartItemCreate(BaseModel):
    book_id: int
    quantity: int = Field(default=1, ge=1)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1)


class CartItemRead(BaseModel):
    cart_item_id: int
    book_id: int
    title: str
    quantity: int


class CartRead(BaseModel):
    cart_id: int
    items: List[CartItemRead]

class CartItemPut(BaseModel):
    quantity: int = Field(..., ge=1)