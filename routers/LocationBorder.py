# routers/LocationBorder.py

from fastapi import APIRouter, HTTPException
from routers.LocationFetcher import LocationFetcher
from routers.AddressParser import AddressParser
from routers.GeometryParser import GeometryParser

router = APIRouter()
geoparser = GeometryParser()
DB_NAME = "bus_db"

@router.get("/backend/selected_coordinates")
def selected_coordinates(address: str):
    parser = AddressParser(DB_NAME)
    fetcher = LocationFetcher(DB_NAME)
    try:
        result = parser.parse(address)
        loc = fetcher.get(result["level"], result["code"])
        multi_poly = geoparser.parse_geometry_to_list(loc["geometry"])
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
        return geoparser.parse_geometry_to_list(loc["geometry"])
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다.")
