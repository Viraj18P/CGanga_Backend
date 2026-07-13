import os
import tempfile
import zipfile

import shapefile
from shapely.geometry import shape, mapping

from database import get_db_connection


# ---------------------------
# Helper: Force any geometry to 2D
# ---------------------------

def force_2d(geom):
    """Convert any geometry to 2D by stripping Z-coordinates."""
    geojson = mapping(geom)

    def strip_z(coords):
        return [(c[0], c[1]) for c in coords]

    gtype = geom.geom_type

    if gtype == "Point":
        x, y, *_ = geojson["coordinates"]
        geojson["coordinates"] = (x, y)

    elif gtype == "MultiPoint":
        geojson["coordinates"] = [(c[0], c[1]) for c in geojson["coordinates"]]

    elif gtype == "LineString":
        geojson["coordinates"] = strip_z(geojson["coordinates"])

    elif gtype == "MultiLineString":
        geojson["coordinates"] = [strip_z(line) for line in geojson["coordinates"]]

    elif gtype == "Polygon":
        geojson["coordinates"] = [strip_z(ring) for ring in geojson["coordinates"]]

    elif gtype == "MultiPolygon":
        geojson["coordinates"] = [
            [strip_z(ring) for ring in poly]
            for poly in geojson["coordinates"]
        ]

    return shape(geojson)


# ---------------------------
# 1. Insert Groundwater Point
# ---------------------------

async def add_groundwater_point(lat: float, lon: float, water_level: float, district: str):
    conn = await get_db_connection()
    if not conn:
        return {"error": "DB connection failed"}

    try:
        async with conn.transaction():
            geom = f"POINT({lon} {lat})"

            is_valid = await conn.fetchval(
                "SELECT ST_IsValid(ST_GeomFromText($1, 4326));",
                geom
            )
            if not is_valid:
                raise Exception("Invalid geometry for groundwater point")

            if water_level < 0 or water_level > 200:
                raise Exception("Water level out of allowed range")

            query = """
                    INSERT INTO ground_water_points
                        (geom, district, rl)
                    VALUES (ST_GeomFromText($1, 4326),
                            $2,
                            $3)
                    RETURNING id; \
                    """

            new_id = await conn.fetchval(query, geom, district, water_level)
            return {"status": "success", "id": new_id}

    except Exception as e:
        return {"error": str(e)}

    finally:
        await conn.close()


# ---------------------------
# 2. Update Stream Metadata
# ---------------------------

async def update_stream_segment(id: int, name: str, remarks: str):
    conn = await get_db_connection()

    if not conn:
        return {"error": "DB connection failed"}

    try:
        async with conn.transaction():

            exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM hindon_stream_network WHERE id=$1);",
                id
            )
            if not exists:
                raise Exception("Stream segment does not exist")

            query = """
                    UPDATE hindon_stream_network
                    SET name    = $2,
                        remarks = $3
                    WHERE id = $1
                    RETURNING id; \
                    """

            updated_id = await conn.fetchval(query, id, name, remarks)
            return {"status": "updated", "id": updated_id}

    except Exception as e:
        return {"error": str(e)}

    finally:
        await conn.close()


# ---------------------------
# 3. Insert Stream Shapefile
# ---------------------------

async def insert_stream_shapefile(uploaded_zip):
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, uploaded_zip.filename)

    with open(zip_path, "wb") as f:
        f.write(await uploaded_zip.read())

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(temp_dir)

    shp_file = None
    for f in os.listdir(temp_dir):
        if f.endswith(".shp"):
            shp_file = os.path.join(temp_dir, f)

    if not shp_file:
        return {"error": "No .shp found in ZIP"}

    sf = shapefile.Reader(shp_file)
    fields = [f[0] for f in sf.fields[1:]]

    conn = await get_db_connection()

    try:
        async with conn.transaction():

            for sr in sf.shapeRecords():
                geom = shape(sr.shape.__geo_interface__)
                geom_2d = force_2d(geom)
                geom_wkt = geom_2d.wkt

                attrs = (
                    sr.record.as_dict()
                    if hasattr(sr.record, "as_dict")
                    else dict(zip(fields, sr.record))
                )

                await conn.execute(
                    """
                    INSERT INTO hindon_stream_network (geom, name, remarks)
                    VALUES (ST_GeomFromText($1, 4326),
                            $2,
                            $3)
                    """,
                    geom_wkt,
                    attrs.get("name"),
                    attrs.get("remarks"),
                )

        return {"status": "success", "inserted": len(sf)}

    except Exception as e:
        return {"error": str(e)}

    finally:
        await conn.close()


# ---------------------------
# 4. Insert Basin Shapefile
# ---------------------------

async def insert_basin_shapefile(uploaded_zip):
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, uploaded_zip.filename)

    with open(zip_path, "wb") as f:
        f.write(await uploaded_zip.read())

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(temp_dir)

    shp_file = None
    for f in os.listdir(temp_dir):
        if f.endswith(".shp"):
            shp_file = os.path.join(temp_dir, f)

    if not shp_file:
        return {"error": "No .shp file found in ZIP"}

    sf = shapefile.Reader(shp_file)

    conn = await get_db_connection()

    try:
        async with conn.transaction():

            for sr in sf.shapeRecords():
                geom = shape(sr.shape.__geo_interface__)
                geom_2d = force_2d(geom)
                geom_wkt = geom_2d.wkt

                await conn.execute(
                    """
                    INSERT INTO hindon_basin (geom)
                    VALUES (ST_GeomFromText($1, 4326))
                    """,
                    geom_wkt
                )

        return {"status": "success", "basin_polygons": len(sf)}

    except Exception as e:
        return {"error": str(e)}

    finally:
        await conn.close()
