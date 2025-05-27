from fastapi import APIRouter, HTTPException
from shapely import wkt
from shapely.geometry import MultiPolygon, Polygon
from routers.LocationFetcher import LocationFetcher
from routers.AddressParser import AddressParser

router = APIRouter()
DB_NAME = "bus_db"

def parse_geometry_to_list(geometry: str):
    polygon = wkt.loads(geometry)
    if isinstance(polygon, MultiPolygon):
        polygon = list(polygon.geoms)[0]
    if isinstance(polygon, Polygon):
        return [{"lat": y, "lng": x} for x, y in list(polygon.exterior.coords)]
    raise HTTPException(status_code=500, detail="지원되지 않는 geometry 형식입니다.")

@router.get("/backend/selected_coordinates")
def selected_coordinates(address: str):
    parser = AddressParser(DB_NAME)
    fetcher = LocationFetcher(DB_NAME)
    try:
        result = parser.parse(address)
        loc = fetcher.get(result["level"], result["code"])
        multi_poly = parse_geometry_to_list(loc["geometry"])
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다.")

    return {
        "coordinates": loc["coordinates"],
        "multiPolygon": multi_poly,
        "matched_level": result["level"],
        "matched_name": result["matched_name"]
    }

@router.get("/backend/naver_polygon")
def naver_polygon(address: str):
    parser = AddressParser(DB_NAME)
    fetcher = LocationFetcher(DB_NAME)
    try:
        result = parser.parse(address)
        loc = fetcher.get(result["level"], result["code"])
        return parse_geometry_to_list(loc["geometry"])
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다.")
