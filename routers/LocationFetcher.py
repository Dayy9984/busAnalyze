from fastapi import APIRouter
from shapely import wkt
from shapely.geometry import MultiPolygon, Polygon
from sqlalchemy import text
from dbmodule import dbmodule

router = APIRouter()


# -------------------------------
# 좌표 + 경계 조회 클래스 (코드 → 데이터)
# -------------------------------
class LocationFetcher:
    def __init__(self,dbname):
        self.DB_NAME = dbname
        self.db = dbmodule() 
        self.engine = self.db.get_db(self.DB_NAME)

    def get(self, level: str, code: str) -> dict:
        with self.engine as conn:
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