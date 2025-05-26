from fastapi import APIRouter
from shapely import wkt
from shapely.geometry import MultiPolygon, Polygon
from sqlalchemy import text
from dbmodule import dbmodule

router = APIRouter()


# -------------------------------
# 주소 파서 클래스 (주소 → 코드)
# -------------------------------
class AddressParser:
    def __init__(self,dbname):
        self.DB_NAME = dbname
        self.db = dbmodule() 
        self.engine = self.db.get_db(self.DB_NAME)

    def parse(self, address: str) -> dict:
        parts = [p.strip() for p in address.strip().split() if p.strip()]

        with self.engine as conn:
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