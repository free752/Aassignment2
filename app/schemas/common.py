

from app.schemas.authors import AuthorRead
from app.schemas.users import UserRead
from app.schemas.favorites import FavoriteRead
from pydantic import BaseModel
from typing import List
from app.schemas.orders import OrderRead

class UserListPage(BaseModel):
    content: List[UserRead]
    page: int
    size: int
    totalElements: int
    totalPages: int
    sort: str


class AuthorListPage(BaseModel):
    content: List[AuthorRead]
    page: int
    size: int
    totalElements: int
    totalPages: int
    sort: str


class OrderListPage(BaseModel):
    content: List[OrderRead]
    page: int
    size: int
    totalElements: int
    totalPages: int
    sort: str

class FavoriteListPage(BaseModel):
    content: List[FavoriteRead]
    page: int
    size: int
    totalElements: int
    totalPages: int
    sort: str