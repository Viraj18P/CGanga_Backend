from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from database import Base, engine
from models import User
from schemas import UserCreate, ShowUser
import crud
from crud import *
from crud_transactions import *
from utils import generate_verification_token
from auth import authenticate_user, create_access_token, get_db



Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Hindon Geospatial Data API",
    servers=[{"url": "http://127.0.0.1:8000", "description": "Local dev server"}]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:5173"] if using Vite
    allow_credentials=True,
    allow_methods=["*"],  # very important
    allow_headers=["*"],  # very important
)
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
    
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}




@app.get("/", tags=["Root"])
async def read_root():
    """A simple welcome message for the API root."""
    return {"message": "Welcome to the Hindon Geospatial Data API!"}

# --- API Endpoints for Your Geospatial Data ---

@app.get("/api/ground_water_points", tags=["Geospatial Data"])
async def get_ground_water_points():
    """Fetches all ground water points as GeoJSON."""
    return await crud.get_all_geodata_from_table("ground_water_points")

@app.get("/api/hindon_basin", tags=["Geospatial Data"])
async def get_hindon_basin():
    """Fetches the Hindon basin polygon as GeoJSON."""
    return await crud.get_all_geodata_from_table("hindon_basin")

@app.get("/api/hindon_stream_network", tags=["Geospatial Data"])
async def get_hindon_stream_network():
    """Fetches the Hindon stream network as GeoJSON."""
    return await crud.get_all_geodata_from_table("hindon_stream_network")

@app.get("/api/ugc_stations", tags=["Geospatial Data"])
async def get_ugc_stations():
    """Fetches all UGC stations as GeoJSON."""
    return await crud.get_all_geodata_from_table("ugc_stations")


@app.post("/api/add_groundwater_point")
async def add_groundwater(lat: float, lon: float, water_level: float, district: str = ""):
    return await add_groundwater_point(lat, lon, water_level, district)


@app.put("/api/update_stream")
async def update_stream(id: int, name: str, remarks: str = ""):
    return await update_stream_segment(id, name, remarks)



@app.post("/api/upload_stream_shapefile")
async def upload_stream_shapefile(file: UploadFile = File(...)):
    return await insert_stream_shapefile(file)

@app.post("/api/upload_basin_shapefile")
async def upload_basin_shapefile(file: UploadFile = File(...)):
    return await insert_basin_shapefile(file)