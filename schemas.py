from pydantic import BaseModel, EmailStr
from datetime import datetime
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class ShowUser(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_verified: bool

    class Config:
        orm_mode = True
        from_attributes = True        

#---------------------------------
class PostBase(BaseModel):
     title: str
     content: str
     username: str
     image: str | None = None

class PostCreate(PostBase):
     pass

class ShowPost(PostBase):
     id: int
     date: datetime

     class Config:
        from_attributes = True


class GalleryBase(BaseModel):
     src: str
     caption: str

class GalleryCreate(GalleryBase):
     pass

class ShowGallery(GalleryBase):
     id: int

     class Config:
         from_attributes = True


class EventBase(BaseModel):
    name: str
    date: str
    location: str

class EventCreate(EventBase):
     pass

class ShowEvent(EventBase):
    id: int

    class Config:
        from_attributes = True
