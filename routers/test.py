from fastapi import APIRouter
from shapely import wkt
from shapely.geometry import MultiPolygon, Polygon
from sqlalchemy import text
from dbmodule import engine

router = APIRouter()

# -------------------------------
# 🎯 1. 주소 파서 클래스 (주소 → 코드)
# -------------------------------
class AddressParser:
    def __init__(self):
        self.engine = engine

    def parse(self, address: str) -> dict:
        parts = [p.strip() for p in address.strip().split() if p.strip()]

        with self.engine.connect() as conn:
            gu_list = [r[0] for r in conn.execute(text("SELECT SIG_KOR_NM FROM SIG_CODE")).fetchall()]
            dong_list = [r[0] for r in conn.execute(text("SELECT DISTINCT EMD_KOR_NM FROM EMD_CODE")).fetchall()]

            # 👇 접두어 기반 자동 완성
            def complete_part(part, candidates):
                return next((c for c in candidates if c.startswith(part)), part)

            if len(parts) >= 2:
                gu_name = complete_part(parts[-2], gu_list)
                dong_name = complete_part(parts[-1], dong_list)
            elif len(parts) == 1:
                gu_name = complete_part(parts[0], gu_list)
                dong_name = None
            else:
                raise ValueError("주소 형식이 올바르지 않습니다.")

            gu = conn.execute(
                text("SELECT SIG_CD, SIG_KOR_NM FROM SIG_CODE WHERE SIG_KOR_NM = :gu"),
                {"gu": gu_name}
            ).fetchone()

            if not gu:
                return {}

            sig_cd, sig_nm = gu

            if dong_name:
                dong = conn.execute(
                    text("""
                        SELECT EMD_CD, EMD_KOR_NM FROM EMD_CODE 
                        WHERE EMD_KOR_NM = :dong AND LEFT(EMD_CD, 5) = :sig_cd
                    """),
                    {"dong": dong_name, "sig_cd": sig_cd}
                ).fetchone()

                if dong:
                    return {
                        "level": "동",
                        "code": dong[0],
                        "matched_name": f"{sig_nm} {dong[1]}"
                    }

            return {
                "level": "구",
                "code": sig_cd,
                "matched_name": sig_nm
            }

# -------------------------------
# 📍 2. 좌표 + 경계 조회 클래스 (코드 → 데이터)
# -------------------------------
class LocationFetcher:
    def __init__(self):
        self.engine = engine

    def get(self, level: str, code: str) -> dict:
        with self.engine.connect() as conn:
            if level == "동":
                coord = conn.execute(
                    text("SELECT longitude, latitude FROM coords WHERE emd_nm = (SELECT EMD_KOR_NM FROM emd_code WHERE EMD_CD = :code LIMIT 1)"),
                    {"code": code}
                ).fetchone()
                geometry = conn.execute(
                    text("SELECT geometry FROM umd WHERE EMD_CD = :code"),
                    {"code": code}
                ).scalar()
            elif level == "구":
                coord = conn.execute(
                    text("SELECT longitude, latitude FROM coords WHERE sig_nm = (SELECT SIG_KOR_NM FROM sig_code WHERE SIG_CD = :code LIMIT 1) AND emd_nm IS NULL"),
                    {"code": code}
                ).fetchone()
                geometry = conn.execute(
                    text("SELECT geometry FROM sgg WHERE ADM_SECT_C = :code"),
                    {"code": code}
                ).scalar()
            else:
                raise ValueError("레벨은 '동' 또는 '구'여야 합니다.")

        if not coord or not geometry:
            raise ValueError("좌표 또는 geometry를 찾을 수 없습니다.")
        return {"coordinates": [coord[0], coord[1]], "geometry": geometry}

# -------------------------------
# 🧭 3. geometry 파싱 함수
# -------------------------------
def parse_geometry_to_list(geometry: str):
    polygon = wkt.loads(geometry)
    if isinstance(polygon, MultiPolygon):
        polygon = list(polygon.geoms)[0]
    if isinstance(polygon, Polygon):
        return [{"lat": y, "lng": x} for x, y in list(polygon.exterior.coords)]
    raise ValueError("지원되지 않는 geometry 형식입니다.")

# -------------------------------
# 🚦 4. /backend/selected_coordinates
# -------------------------------
@router.get("/backend/selected_coordinates")
def selected_coordinates(address: str):
    parser = AddressParser()
    result = parser.parse(address)
    fetcher = LocationFetcher()
    loc = fetcher.get(result["level"], result["code"])
    return {
        "coordinates": loc["coordinates"],
        "multiPolygon": parse_geometry_to_list(loc["geometry"]),
        "matched_level": result["level"],
        "matched_name": result["matched_name"]
    }

# -------------------------------
# 🚦 5. /backend/naver_polygon
# -------------------------------
@router.get("/backend/naver_polygon")
def naver_polygon(address: str):
    parser = AddressParser()
    result = parser.parse(address)
    fetcher = LocationFetcher()
    loc = fetcher.get(result["level"], result["code"])
    return parse_geometry_to_list(loc["geometry"])
