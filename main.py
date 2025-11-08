from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import crud
from crud_transactions import (
    add_groundwater_point,
    update_stream_segment,
    insert_stream_shapefile,
    insert_basin_shapefile,
)


app = FastAPI(title="Hindon GeoAPI")

# CORS middleware allows the frontend (on a different address) to access this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
