# app/schemas/favorites.py
from pydantic import BaseModel


class FavoriteCreate(BaseModel):
    book_id: int


class FavoriteRead(BaseModel):
    book_id: int
    title: str

    class Config:
        from_attributes = True