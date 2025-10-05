import json
from database import get_db_connection

async def format_records_as_geojson(records):
    """Helper function to format records into a GeoJSON FeatureCollection."""
    features = []
    for record in records:
        geometry = json.loads(record['geom_geojson'])
        properties = {key: value for key, value in record.items() if key != 'geom_geojson'}

        features.append({
            "type": "Feature",
            "geometry": geometry,
            "properties": properties
        })
    
    return {
        "type": "FeatureCollection",
        "features": features
    }

async def get_all_geodata_from_table(table_name: str):
    """Fetches all records from a given table and returns them as GeoJSON."""
    conn = await get_db_connection()
    if not conn:
        return {"error": "Database connection failed"}
    
    try:
        # The core SQL query that converts geometry to GeoJSON
        query = f"""
            SELECT *, ST_AsGeoJSON(geom) as geom_geojson
            FROM {table_name};
        """
        records = await conn.fetch(query)
        geojson_data = await format_records_as_geojson(records)
        return geojson_data
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            await conn.close()