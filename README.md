# Hindon GeoAPI (CGanga Backend)

A small FastAPI backend that serves geospatial data (PostGIS) and provides endpoints to upload shapefiles (zipped), add
groundwater points, and update stream metadata.

Frontend: https://github.com/saranshhalwai/Cgangafrontend

## Summary

This project exposes geospatial tables as GeoJSON and includes transactional helpers to insert shapefiles into PostGIS
and add/update features. It expects a PostgreSQL database with PostGIS enabled.

Key features

- Serve GeoJSON from PostGIS tables
- Add groundwater points via API
- Update stream segment metadata
- Upload zipped shapefiles for stream network and basin polygons

## Requirements

- Python 3.8+
- PostgreSQL with PostGIS extension

Python dependencies (see `requirements.txt`):

- fastapi
- uvicorn[standard]
- asyncpg
- python-dotenv
- shapely
- pyshp (shapefile)

If any of these are missing, install them with pip.

## Quick start

1. Create and enable PostGIS on your PostgreSQL database.
2. Create the expected tables (see Schema below).
3. Create a `.env` file at the project root with your `DATABASE_URL` (example below).
4. Install Python dependencies and run the server.

Example `.env`:

DATABASE_URL=postgresql://user:password@localhost:5432/your_database

Install and run:

```bash
python -m pip install -r requirements.txt
# install extras if needed
python -m pip install shapely pyshp python-dotenv

uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open http://127.0.0.1:8000/docs for automatic API docs (Swagger UI).

## Expected database schema (example)

The code references the following tables. Create them as appropriate; these are minimal examples.

- ground_water_points
    - id SERIAL PRIMARY KEY
    - geom geometry(Point, 4326)
    - district TEXT
    - rl FLOAT -- water level

- hindon_stream_network
    - id SERIAL PRIMARY KEY
    - geom geometry(LineString, 4326)
    - name TEXT
    - remarks TEXT

- hindon_basin
    - id SERIAL PRIMARY KEY
    - geom geometry(Polygon, 4326)

- ugc_stations
    - id SERIAL PRIMARY KEY
    - geom geometry(Point, 4326)
    - (other station attributes as needed)

Adjust column names/types if your schema differs; the backend uses these names in SQL queries.

## Environment variables

- DATABASE_URL: Full asyncpg-compatible connection string. The project uses python-dotenv to load `.env`.

## API Endpoints

Base URL: http://<host>:<port>

- GET / (Root)
    - Returns a welcome message.

- GET /api/ground_water_points
    - Returns all records from `ground_water_points` as a GeoJSON FeatureCollection.

- GET /api/hindon_basin
    - Returns all `hindon_basin` geometries as GeoJSON.

- GET /api/hindon_stream_network
    - Returns all stream features from `hindon_stream_network` as GeoJSON.

- GET /api/ugc_stations
    - Returns all UGC stations as GeoJSON.

- POST /api/add_groundwater_point
    - Query parameters: `lat` (float), `lon` (float), `water_level` (float), `district` (optional string)
    - Example:
      ```bash
      curl -X POST "http://127.0.0.1:8000/api/add_groundwater_point?lat=28.0&lon=77.5&water_level=12.3&district=Ghaziabad"
      ```
    - Returns JSON with `status` and new `id` on success.

- PUT /api/update_stream
    - Query parameters: `id` (int), `name` (string), `remarks` (optional string)
    - Example:
      ```bash
      curl -X PUT "http://127.0.0.1:8000/api/update_stream?id=12&name=NewName&remarks=Updated"
      ```

- POST /api/upload_stream_shapefile
    - Form upload: a ZIP file containing the shapefile (must include `.shp`). The endpoint reads the ZIP, extracts
      `.shp` and inserts features into `hindon_stream_network`.
    - Example using curl (form upload):
      ```bash
      curl -X POST -F "file=@stream_shapefile.zip" http://127.0.0.1:8000/api/upload_stream_shapefile
      ```

- POST /api/upload_basin_shapefile
    - Similar to the stream upload but inserts into `hindon_basin`.

## Shapefile upload notes

- Provide a ZIP that contains at least the `.shp` file. Recommended to include `.shx`, `.dbf`, `.prj` alongside `.shp`.
- The code uses `pyshp` (shapefile.Reader) and `shapely` to convert geometries.
- Z coordinates (3D) are stripped to 2D before insertion.
- For the stream shapefile the implementation attempts to read attributes `name` and `remarks` from the shapefile
  records. If your attribute names differ, modify `crud_transactions.py` accordingly.

## Error handling & edge cases

- If `DATABASE_URL` is missing or invalid, the server will print a DB connection error and endpoints that require DB
  access will return an error JSON.
- Shapefile ZIP missing a `.shp` will return an error.
- Groundwater point insertion validates geometry and enforces a simple water level range check (0–200); adjust as
  needed.

## Development notes

- Main entrypoint: `main.py` (FastAPI app instance).
- Database connection helper: `database.py` (asyncpg). Ensure the `DATABASE_URL` works with asyncpg.
- GeoJSON conversion: `crud.py` builds FeatureCollection responses by using `ST_AsGeoJSON(geom)` in SQL.
- Transactional operations and shapefile insertion live in `crud_transactions.py`.

## Frontend

The frontend for this backend lives at:

https://github.com/saranshhalwai/Cgangafrontend

Clone or view the frontend repo to see how it consumes these endpoints.

## Troubleshooting

- Check `.env` and ensure `DATABASE_URL` is present and points to a PostGIS-enabled database.
- If you get geometry errors, verify the input shapefile CRS and coordinate order. The backend assumes EPSG:4326.
- Large shapefiles may take time to insert; consider batching or increasing server timeouts.

## License

This repository follows the included LICENSE file. See `LICENSE` for details.
