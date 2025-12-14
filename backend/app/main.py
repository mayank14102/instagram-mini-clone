from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from typing import List

from .database import engine, create_db_and_tables, get_session
from .models import User, Post, Like, Follow, Comment
from .schemas import UserCreate, UserLogin, UserRead, Token, PostCreate, PostRead, CommentCreate, CommentRead
from .auth import get_password_hash, verify_password, create_access_token, get_current_user


app = FastAPI(title="Instagram Mini Clone Backend")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


create_db_and_tables()


@app.post("/api/auth/register", response_model=Token)
def register(user_data: UserCreate, session: Session = Depends(get_session)):
    # check unique email/username
    existing = session.exec(select(User).where((User.email == user_data.email) | (User.username == user_data.username))).first()
    if existing:
        raise HTTPException(status_code=400, detail="username or email already taken")
    user = User(username=user_data.username, email=user_data.email, password_hash=get_password_hash(user_data.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


@app.post("/api/auth/login", response_model=Token)
def login(form_data: UserLogin, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == form_data.email)).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/api/users/me", response_model=UserRead)
def read_profile(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    follower_count = session.exec(select(Follow).where(Follow.following_id == current_user.id)).count()
    following_count = session.exec(select(Follow).where(Follow.follower_id == current_user.id)).count()
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "follower_count": follower_count,
        "following_count": following_count,
    }


@app.post("/api/users/{user_id}/follow")
def follow_user(user_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    if current_user.id == user_id:
        raise HTTPException(400, "cannot follow yourself")
    existing = session.exec(select(Follow).where(Follow.follower_id == current_user.id, Follow.following_id == user_id)).first()
    if existing:
        return {"detail": "already following"}
    follow = Follow(follower_id=current_user.id, following_id=user_id)
    session.add(follow)
    session.commit()
    return {"detail": "followed"}


@app.post("/api/users/{user_id}/unfollow")
def unfollow_user(user_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    existing = session.exec(select(Follow).where(Follow.follower_id == current_user.id, Follow.following_id == user_id)).first()
    if not existing:
        return {"detail": "not following"}
    session.delete(existing)
    session.commit()
    return {"detail": "unfollowed"}


@app.post("/api/posts", response_model=PostRead)
def create_post(post_data: PostCreate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    post = Post(author_id=current_user.id, image_url=post_data.image_url, caption=post_data.caption)
    session.add(post)
    session.commit()
    session.refresh(post)
    return PostRead(
        id=post.id,
        author_id=post.author_id,
        image_url=post.image_url,
        caption=post.caption,
        created_at=post.created_at,
        like_count=0,
        comment_count=0,
    )


@app.get("/api/posts/{post_id}", response_model=PostRead)
def get_post(post_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    post = session.get(Post, post_id)
    if not post:
        raise HTTPException(404, "post not found")
    like_count = session.exec(select(Like).where(Like.post_id == post_id)).count()
    comment_count = session.exec(select(Comment).where(Comment.post_id == post_id)).count()
    return PostRead(
        id=post.id,
        author_id=post.author_id,
        image_url=post.image_url,
        caption=post.caption,
        created_at=post.created_at,
        like_count=like_count,
        comment_count=comment_count,
    )


@app.get("/api/posts", response_model=List[PostRead])
def list_posts(page: int = 1, limit: int = 20, session: Session = Depends(get_session)):
    skip = (page - 1) * limit
    posts = session.exec(select(Post).order_by(Post.created_at.desc()).offset(skip).limit(limit)).all()
    results = []
    for post in posts:
        like_count = session.exec(select(Like).where(Like.post_id == post.id)).count()
        comment_count = session.exec(select(Comment).where(Comment.post_id == post.id)).count()
        results.append(PostRead(
            id=post.id,
            author_id=post.author_id,
            image_url=post.image_url,
            caption=post.caption,
            created_at=post.created_at,
            like_count=like_count,
            comment_count=comment_count,
        ))
    return results


@app.post("/api/posts/{post_id}/like")
def like_post(post_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    existing = session.exec(select(Like).where(Like.user_id == current_user.id, Like.post_id == post_id)).first()
    if existing:
        # already like
        return {"detail": "already liked"}
    like = Like(user_id=current_user.id, post_id=post_id)
    session.add(like)
    session.commit()
    return {"detail": "liked"}


@app.post("/api/posts/{post_id}/unlike")
def unlike_post(post_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    existing = session.exec(select(Like).where(Like.user_id == current_user.id, Like.post_id == post_id)).first()
    if not existing:
        return {"detail": "not liked"}
    session.delete(existing)
    session.commit()
    return {"detail": "unliked"}


@app.post("/api/posts/{post_id}/comments", response_model=CommentRead)
def create_comment(post_id: int, comment_in: CommentCreate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    post = session.get(Post, post_id)
    if not post:
        raise HTTPException(404, "post not found")
    comment = Comment(user_id=current_user.id, post_id=post_id, content=comment_in.content)
    session.add(comment)
    session.commit()
    session.refresh(comment)
    return CommentRead(
        id=comment.id,
        user_id=comment.user_id,
        post_id=comment.post_id,
        content=comment.content,
        created_at=comment.created_at,
    )


@app.get("/api/posts/{post_id}/comments", response_model=List[CommentRead])
def list_comments(post_id: int, session: Session = Depends(get_session)):
    comments = session.exec(select(Comment).where(Comment.post_id == post_id).order_by(Comment.created_at)).all()
    return [CommentRead(**c.dict()) for c in comments]


@app.get("/api/feed", response_model=List[PostRead])
def get_feed(limit: int = 20, page: int = 1, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    # grab user ids that current user follows
    following = session.exec(select(Follow.following_id).where(Follow.follower_id == current_user.id)).all()
    # include user's own id
    ids = [current_user.id] + [f[0] if isinstance(f, tuple) else f for f in following]
    skip = (page - 1) * limit
    posts = session.exec(select(Post).where(Post.author_id.in_(ids)).order_by(Post.created_at.desc()).offset(skip).limit(limit)).all()
    results = []
    for post in posts:
        like_count = session.exec(select(Like).where(Like.post_id == post.id)).count()
        comment_count = session.exec(select(Comment).where(Comment.post_id == post.id)).count()
        results.append(PostRead(
            id=post.id,
            author_id=post.author_id,
            image_url=post.image_url,
            caption=post.caption,
            created_at=post.created_at,
            like_count=like_count,
            comment_count=comment_count,
        ))
    return results

