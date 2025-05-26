from fastapi import APIRouter
from shapely import wkt
from shapely.geometry import MultiPolygon, Polygon
from sqlalchemy import text
from dbmodule import dbmodule
from routers.AddressParser import AddressParser

router = APIRouter()
DB_NAME = "bus_db"

@router.get("/backend/smart_bus")
def smart_bus(address: str):
    parser = AddressParser(DB_NAME)
    db = dbmodule()
    engine = db.get_db_con(DB_NAME)
    result = parser.parse(address)
    level, code = result["level"], result["code"]


    json = {"smartBus": []}

    with engine.connect() as conn:
        if level == "동":
            rows = conn.execute(
                text("SELECT * FROM smart_bus_station WHERE umd_code = :code"),
                {"code": code}
            ).fetchall()
        elif level == "구":
            rows = conn.execute(
                text("SELECT * FROM smart_bus_station WHERE sgg_code = :code"),
                {"code": code}
            ).fetchall()
        else:
            raise ValueError("레벨은 '동' 또는 '구'여야 합니다.")

    for row in rows:
        json["smartBus"].append({
            "id": row.id,
            "station_name": row.station_name,
            "line_num": row.line_num,
            "arsno": row.arsno,
            "lat": row.lat,
            "lon": row.lon,
            "score": row.score,
            "rank": row.rank
        })


    if not json["smartBus"]:
        raise ValueError("smartBus 데이터를 찾을 수 없습니다.")

    return json
