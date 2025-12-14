from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List


class Follow(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    follower_id: int = Field(foreign_key="user.id")
    following_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    posts: List["Post"] = Relationship(back_populates="author")


class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    author_id: int = Field(foreign_key="user.id")
    image_url: str
    caption: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    author: Optional[User] = Relationship(back_populates="posts")
    likes: List["Like"] = Relationship(back_populates="post")
    comments: List["Comment"] = Relationship(back_populates="post")


class Like(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    post_id: int = Field(foreign_key="post.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    post: Optional[Post] = Relationship(back_populates="likes")


class Comment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    post_id: int = Field(foreign_key="post.id")
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    post: Optional[Post] = Relationship(back_populates="comments")
