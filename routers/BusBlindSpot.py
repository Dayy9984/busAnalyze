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

def parse_geometry_to_list(geometry: str) -> list:
    polygon = wkt.loads(geometry)
    if isinstance(polygon, MultiPolygon):
        polygons = list(polygon.geoms)
    else:
        polygons = [polygon]
    result = []
    for poly in polygons:
        if isinstance(poly, Polygon):
            coords = list(poly.exterior.coords)
            result.append([{"lat": y, "lng": x} for x, y in coords])
    return result

@router.get("/backend/bus_blind_spot")
def get_bus_blind_spot(address: str = None):
    parser = AddressParser(DB_NAME)
    db = dbmodule()
    engine = db.get_db_con(DB_NAME)

    json = {"BusBlindSpot": []}

    with engine.connect() as conn:
        # 1. address가 없거나 "부산광역시"일 때 전체 데이터 반환
        if not address or address.strip() == "부산광역시":
            rows = conn.execute(
                text("SELECT * FROM bus_blind_spot_ranked")
            ).fetchall()
        else:
            result = parser.parse(address)
            level, code = result["level"], result["code"]
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
        polygon_coords = parse_geometry_to_list(row.geometry)
        json["BusBlindSpot"].append({
            "id": row.id,
            "polygon": row.geometry,
            "polygon_coords": polygon_coords,
            "lat": row.lat,
            "lon": row.lon,
            "score": row.score,
            "rank": row.rank
        })

    if not json["BusBlindSpot"]:
        raise ValueError("BusBlindSpot 데이터를 찾을 수 없습니다.")

    return json
