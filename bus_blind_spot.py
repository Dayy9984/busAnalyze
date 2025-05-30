from fastapi import APIRouter, Query, HTTPException, Path
from pydantic import BaseModel
from shapely import wkt
from shapely.geometry import MultiPolygon, Polygon
from sqlalchemy import text
from dbmodule import dbmodule
from routers.AddressParser import AddressParser

router = APIRouter()
DB_NAME = "bus_db"

# --- Pydantic Models ---
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

# -------------------------------
# GET  /backend/bus_blind_spot
# -------------------------------
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

# -------------------------------
# POST /backend/bus_blind_spot
# -------------------------------
@router.post("/backend/bus_blind_spot")
def create_bus_blind_spot(item: BlindSpotCreate):
    db = dbmodule()
    engine = db.get_db_con(DB_NAME)
    sql = (
        "INSERT INTO bus_blind_spot_ranked "
        "(sgg_code, umd_code, geometry, lat, lon, score, `rank`) "
        "VALUES (:sgg_code, :umd_code, :geometry, :lat, :lon, :score, :rank)"
    )
    with engine.begin() as conn:
        conn.execute(text(sql), item.dict())
    return {"message": "BusBlindSpot created"}

# -------------------------------
# PUT  /backend/bus_blind_spot/{id}
# -------------------------------

@router.put("/backend/bus_blind_spot/{id}")
def update_bus_blind_spot(
    id: int = Path(..., description="BusBlindSpot ID"),
    item: BlindSpotUpdate = None
):
    db = dbmodule()
    engine = db.get_db_con(DB_NAME)
    fields, params = [], {"id": id}
    if item.geometry is not None:
        fields.append("geometry = :geometry")
        params["geometry"] = item.geometry
    if item.lat is not None:
        fields.append("lat = :lat")
        params["lat"] = item.lat
    if item.lon is not None:
        fields.append("lon = :lon")
        params["lon"] = item.lon
    if item.score is not None:
        fields.append("score = :score")
        params["score"] = item.score
    if item.rank is not None:
        fields.append("`rank` = :rank")
        params["rank"] = item.rank
    if not fields:
        raise HTTPException(status_code=400, detail="No fields provided for update")
    sql = f"UPDATE bus_blind_spot_ranked SET {', '.join(fields)} WHERE id = :id"
    with engine.begin() as conn:
        result = conn.execute(text(sql), params)
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="BusBlindSpot not found")
    return {"message": "BusBlindSpot updated"}
