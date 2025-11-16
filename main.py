from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from auth import authenticate_user, create_access_token, get_db
from crud import create_user, get_user_by_username, logs
from crud import get_all_geodata_from_table
from crud_transactions import insert_basin_shapefile, insert_stream_shapefile, update_stream_segment, \
    add_groundwater_point
from database import Base, engine
from models import User
from schemas import UserCreate, ShowUser

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:5173"] if using Vite
    allow_credentials=True,
    allow_methods=["*"],  # very important
    allow_headers=["*"],  # very important
)


# Helper: convert backend {'error': msg} into proper HTTP responses
def _check_and_raise(result):
    """If result is a dict with an 'error' key, raise HTTPException with an appropriate status code.

    Heuristics:
    - Database connection failures and internal exceptions -> 500
    - Validation / not found / client errors -> 400
    """
    if isinstance(result, dict) and "error" in result:
        msg = str(result.get("error"))
        low = msg.lower()
        if "db connection" in low or "connection failed" in low or "exception" in low or "traceback" in low:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg)
        if "not found" in low or "does not exist" in low or "invalid" in low or "out of allowed" in low:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
        # fallback to 400 for other errors coming from business logic
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    return result


@app.post("/register", response_model=ShowUser)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return create_user(db, user)


@app.get("/verify/{token}")
def verify_email(token: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.verification_token == token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link")

    user.is_verified = True
    user.verification_token = None
    db.commit()
    return {"message": "Email verified successfully!"}


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token({"sub": user.username, "role": user.role})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/")
def root():
    return {"message": "FastAPI Auth system working!"}


@app.get("/", tags=["Root"])
async def read_root():
    """A simple welcome message for the API root."""
    return {"message": "Welcome to the Hindon Geospatial Data API!"}


# --- API Endpoints for Your Geospatial Data ---

@app.get("/api/ground_water_points", tags=["Geospatial Data"])
async def get_ground_water_points():
    """Fetches all ground water points as GeoJSON."""
    result = await get_all_geodata_from_table("ground_water_points")
    return _check_and_raise(result)


@app.get("/api/hindon_basin", tags=["Geospatial Data"])
async def get_hindon_basin():
    """Fetches the Hindon basin polygon as GeoJSON."""
    result = await get_all_geodata_from_table("hindon_basin")
    return _check_and_raise(result)


@app.get("/api/hindon_stream_network", tags=["Geospatial Data"])
async def get_hindon_stream_network():
    """Fetches the Hindon stream network as GeoJSON."""
    result = await get_all_geodata_from_table("hindon_stream_network")
    return _check_and_raise(result)


@app.get("/api/ugc_stations", tags=["Geospatial Data"])
async def get_ugc_stations():
    """Fetches all UGC stations as GeoJSON."""
    result = await get_all_geodata_from_table("ugc_stations")
    return _check_and_raise(result)


@app.post("/api/add_groundwater_point")
async def add_groundwater(lat: float, lon: float, water_level: float, district: str = ""):
    result = await add_groundwater_point(lat, lon, water_level, district)
    return _check_and_raise(result)


@app.put("/api/update_stream")
async def update_stream(id: int, name: str, remarks: str = ""):
    result = await update_stream_segment(id, name, remarks)
    return _check_and_raise(result)


@app.post("/api/upload_stream_shapefile")
async def upload_stream_shapefile(file: UploadFile = File(...)):
    result = await insert_stream_shapefile(file)
    return _check_and_raise(result)


@app.post("/api/upload_basin_shapefile")
async def upload_basin_shapefile(file: UploadFile = File(...)):
    result = await insert_basin_shapefile(file)
    return _check_and_raise(result)


@app.get("/simple_user")
def get_simple_user(db: Session = Depends(get_db)):
    """
    Returns first user from the database.
    This is unprotected, no token required.
    """
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="No user found")

    return {
        "username": user.username,
        "email": user.email
    }


from crud_posts import (
    create_post, get_all_posts, update_post, delete_post,
    create_gallery_item, get_gallery_items,
    create_event, get_events, delete_event
)
from schemas import PostCreate, GalleryCreate, EventCreate, ShowEvent, ShowGallery, ShowPost


@app.post("/posts", response_model=ShowPost)
def api_create_post(data: PostCreate, db: Session = Depends(get_db)):
    return create_post(db, data)


@app.get("/posts", response_model=list[ShowPost])
def api_get_posts(db: Session = Depends(get_db)):
    return get_all_posts(db)


@app.put("/posts/{post_id}", response_model=ShowPost)
def api_update_post(post_id: int, data: PostCreate, db: Session = Depends(get_db)):
    updated = update_post(db, post_id, data)
    if not updated:
        raise HTTPException(404, "Post not found")
    return updated


@app.delete("/posts/{post_id}")
def api_delete_post(post_id: int, db: Session = Depends(get_db)):
    ok = delete_post(db, post_id)
    if not ok:
        raise HTTPException(404, "Post not found")
    return {"message": "Deleted"}


@app.post("/gallery", response_model=ShowGallery)
def api_add_gallery(data: GalleryCreate, db: Session = Depends(get_db)):
    return create_gallery_item(db, data)


@app.get("/gallery", response_model=list[ShowGallery])
def api_get_gallery(db: Session = Depends(get_db)):
    return get_gallery_items(db)


# # ----------------------------
# # EVENTS ENDPOINTS
# # ----------------------------
@app.post("/events", response_model=ShowEvent)
def api_add_event(data: EventCreate, db: Session = Depends(get_db)):
    return create_event(db, data)


@app.get("/events", response_model=list[ShowEvent])
def api_get_events(db: Session = Depends(get_db)):
    return get_events(db)


@app.delete("/events/{id}")
def api_delete_event(id: int, db: Session = Depends(get_db)):
    ok = delete_event(db, id)
    if not ok:
        raise HTTPException(404, "Event not found")
    return {"message": "Deleted"}

@app.get("/logs")
def read_logs():
    return logs()