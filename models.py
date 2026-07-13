from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    role: str = Column(String, default="user")
    hashed_password = Column(String)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    content = Column(Text)
    username = Column(String)
    image = Column(Text, nullable=True)
    date = Column(DateTime, default=datetime.utcnow)


class GalleryItem(Base):
    __tablename__ = "gallery_items"

    id = Column(Integer, primary_key=True, index=True)
    src = Column(Text)
    caption = Column(String)


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    date = Column(String)
    location = Column(String)
