from fastapi import APIRouter, Query, HTTPException, Path
from pydantic import BaseModel
from shapely import wkt
from shapely.geometry import MultiPolygon, Polygon
from sqlalchemy import text
from dbmodule import dbmodule
from routers.AddressParser import AddressParser

router = APIRouter()
DB_NAME = "bus_db"


class BlindSpotCreate(BaseModel):
    sgg_code: str
    umd_code: str
    geometry: str   # WKT polygon
    lat: float
    lon: float
    score: float
    rank: int

class BlindSpotUpdate(BaseModel):
    geometry: str | None = None
    lat: float | None = None
    lon: float | None = None
    score: float | None = None
    rank: int | None = None


@router.get("/backend/bus_blind_spot")
def get_bus_blind_spot(address: str):
    parser = AddressParser(DB_NAME)
    db = dbmodule()
    engine = db.get_db_con(DB_NAME)
    result = parser.parse(address)
    level, code = result["level"], result["code"]


    json = {"BusBlindSpot": []}

    with engine.connect() as conn:
        if level == "동":
            rows = conn.execute(
                text("SELECT * FROM bus_blind_spot_ranked WHERE umd_code = :code"),
                {"code": code}
            ).fetchall()
        elif level == "구":
            rows = conn.execute(
                text("SELECT * FROM bus_blind_spot_ranked WHERE sgg_code = :code"),
                {"code": code}
            ).fetchall()
        else:
            raise ValueError("레벨은 '동' 또는 '구'여야 합니다.")

    for row in rows:
        json["BusBlindSpot"].append({
            "id": row.id,
            "polygon": row.geometry,
            "lat": row.lat,
            "lon": row.lon,
            "score": row.score,
            "rank": row.rank
        })


    if not json["BusBlindSpot"]:
        raise ValueError("BusBlindSpot 데이터를 찾을 수 없습니다.")

    return json

