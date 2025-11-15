from sqlalchemy.orm import Session

from models import Post, GalleryItem, Event
from schemas import PostCreate, GalleryCreate, EventCreate


def create_post(db: Session, data: PostCreate):
    post = Post(**data.dict())
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def get_all_posts(db: Session):
    return db.query(Post).order_by(Post.date.desc()).all()


def update_post(db: Session, post_id: int, data: PostCreate):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        return None

    for key, value in data.dict().items():
        setattr(post, key, value)

    db.commit()
    db.refresh(post)
    return post


def delete_post(db: Session, post_id: int):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        return None
    db.delete(post)
    db.commit()
    return True


def create_gallery_item(db: Session, data: GalleryCreate):
    item = GalleryItem(**data.dict())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_gallery_items(db: Session):
    return db.query(GalleryItem).all()


def create_event(db: Session, data: EventCreate):
    ev = Event(**data.dict())
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev


def get_events(db: Session):
    return db.query(Event).order_by(Event.date.asc()).all()


def delete_event(db: Session, id: int):
    ev = db.query(Event).filter(Event.id == id).first()
    if not ev:
        return None
    db.delete(ev)
    db.commit()
    return True
