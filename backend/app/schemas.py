from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr
    follower_count: int = 0
    following_count: int = 0


class Token(BaseModel):
    access_token: str
    token_type: str


class PostCreate(BaseModel):
    image_url: str
    caption: Optional[str] = None


class PostRead(BaseModel):
    id: int
    author_id: int
    image_url: str
    caption: Optional[str] = None
    created_at: datetime
    like_count: int = 0
    comment_count: int = 0


class CommentCreate(BaseModel):
    content: str


class CommentRead(BaseModel):
    id: int
    user_id: int
    post_id: int
    content: str
    created_at: datetime

