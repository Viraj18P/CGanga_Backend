from sqlalchemy.orm import Session

from models import User
from schemas import UserCreate
from utils import hash_password, generate_verification_token
from verify_email import send_verification_email



def create_user(db: Session, user: UserCreate):
    hashed_pw = hash_password(user.password)
    token = generate_verification_token()
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_pw,
        verification_token=token,
        is_verified=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    send_verification_email(user.email, user.username, token)
    return db_user


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


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
    """Fetches a limited number of records from a given table and returns them as GeoJSON."""
    conn = await get_db_connection()
    if not conn:
        return {"error": "Database connection failed"}

    try:
        # The modified SQL query with the LIMIT clause
        query = f"""
            SELECT *, ST_AsGeoJSON(geom) as geom_geojson
            FROM {table_name}
            LIMIT 5000;
        """
        records = await conn.fetch(query)
        geojson_data = await format_records_as_geojson(records)
        return geojson_data
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            await conn.close()


async def logs():
    statement = "SELECT * FROM logs LIMIT 100"
    conn = await get_db_connection()
    with Session(conn) as session:
        results = session.execute(statement).fetchall()
        return results

