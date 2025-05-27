from fastapi import HTTPException
from fastapi import APIRouter
from shapely import wkt
from shapely.geometry import MultiPolygon, Polygon
from sqlalchemy import text
from dbmodule import dbmodule

router = APIRouter()

class LocationFetcher:
    def __init__(self, dbname):
        self.DB_NAME = dbname
        self.db = dbmodule()
        self.engine = self.db.get_db(self.DB_NAME)

    def get(self, level: str, code: str) -> dict:
        with self.engine as conn:
            # 잘못된 레벨 요청
            if level not in ("동", "구"):
                raise HTTPException(status_code=400, detail="레벨은 '동' 또는 '구'여야 합니다.")

            if level == "동":
                coord = conn.execute(
                    text("SELECT longitude, latitude FROM coords WHERE emd_nm = (SELECT EMD_KOR_NM FROM EMD_CODE WHERE EMD_CD = :code LIMIT 1)"),
                    {"code": code}
                ).fetchone()
                geometry = conn.execute(
                    text("SELECT geometry FROM umd WHERE EMD_CD = :code"),
                    {"code": code}
                ).scalar()

            else: 
                coord = conn.execute(
                    text("SELECT longitude, latitude FROM coords WHERE sig_nm = (SELECT SIG_KOR_NM FROM SIG_CODE WHERE SIG_CD = :code LIMIT 1) AND emd_nm IS NULL"),
                    {"code": code}
                ).fetchone()
                geometry = conn.execute(
                    text("SELECT geometry FROM sgg WHERE ADM_SECT_C = :code"),
                    {"code": code}
                ).scalar()

        if not coord or not geometry:
            raise HTTPException(status_code=404, detail="좌표 또는 경계 정보를 찾을 수 없습니다.")
        return {"coordinates": [coord[0], coord[1]], "geometry": geometry}
