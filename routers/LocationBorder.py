# routers/LocationBorder.py

from fastapi import APIRouter, HTTPException
from shapely import wkt
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import transform
from pyproj import Transformer
from routers.LocationFetcher import LocationFetcher
from routers.AddressParser import AddressParser

router = APIRouter()
DB_NAME = "bus_db"

# EPSG:5179(평면좌표계) → EPSG:4326(위경도) 변환기
transformer = Transformer.from_crs("EPSG:5179", "EPSG:4326", always_xy=True)

def parse_geometry_to_list(geometry: str):
    # 1. WKT → Shapely 객체
    polygon = wkt.loads(geometry)
    # 2. 좌표계 변환
    transformed_polygon = transform(transformer.transform, polygon)
    # 3. Polygon/MultiPolygon 처리
    if isinstance(transformed_polygon, MultiPolygon):
        polygons = list(transformed_polygon.geoms)
    else:
        polygons = [transformed_polygon]
    # 4. [ {lat, lng}, ... ] 배열로 변환
    result = []
    for poly in polygons:
        if isinstance(poly, Polygon):
            coords = list(poly.exterior.coords)
            result.append([{"lat": y, "lng": x} for x, y in coords])
    return result

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

    # 중심좌표 [경도, 위도] → [위도, 경도]로 변환 (필요시)
    coordinates = loc["coordinates"]
    if coordinates and len(coordinates) == 2:
        coordinates = [coordinates[1], coordinates[0]]

    return {
        "coordinates": coordinates,
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
