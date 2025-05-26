from fastapi import APIRouter
from shapely import wkt
from shapely.geometry import MultiPolygon, Polygon
from sqlalchemy import text
from routers.LocationFetcher import LocationFetcher
from routers.AddressParser import AddressParser

router = APIRouter()
DB_NAME = "bus_db"

# -------------------------------
# geometry 파싱 함수
# -------------------------------
def parse_geometry_to_list(geometry: str):
    polygon = wkt.loads(geometry)
    if isinstance(polygon, MultiPolygon):
        polygon = list(polygon.geoms)[0]
    if isinstance(polygon, Polygon):
        return [{"lat": y, "lng": x} for x, y in list(polygon.exterior.coords)]
    raise ValueError("지원되지 않는 geometry 형식입니다.")

# -------------------------------
# /backend/selected_coordinates
# -------------------------------
@router.get("/backend/selected_coordinates")
def selected_coordinates(address: str):
    parser = AddressParser(DB_NAME)
    result = parser.parse(address)
    fetcher = LocationFetcher(DB_NAME)
    loc = fetcher.get(result["level"], result["code"])
    return {
        "coordinates": loc["coordinates"],
        "multiPolygon": parse_geometry_to_list(loc["geometry"]),
        "matched_level": result["level"],
        "matched_name": result["matched_name"]
    }

# -------------------------------
# /backend/naver_polygon
# -------------------------------
@router.get("/backend/naver_polygon")
def naver_polygon(address: str):
    parser = AddressParser(DB_NAME)
    result = parser.parse(address)
    fetcher = LocationFetcher(DB_NAME)
    loc = fetcher.get(result["level"], result["code"])
    return parse_geometry_to_list(loc["geometry"])
