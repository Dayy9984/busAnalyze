from fastapi import HTTPException
from fastapi import APIRouter
from shapely import wkt
from shapely.geometry import MultiPolygon, Polygon
from sqlalchemy import text
from dbmodule import dbmodule

router = APIRouter()

class AddressParser:
    def __init__(self, dbname):
        self.DB_NAME = dbname
        self.db = dbmodule()
        self.engine = self.db.get_db(self.DB_NAME)

    def parse(self, address: str) -> dict:
        parts = [p.strip() for p in address.strip().split() if p.strip()]
        if not parts:
            raise HTTPException(status_code=400, detail="주소 형식이 올바르지 않습니다.")

        # 1) 부산광역시 외 처리
        city_aliases = ["부산", "부산시", "부산광역시"]
        if parts[0] not in city_aliases:
            raise HTTPException(status_code=400, detail="부산광역시 주소만 지원합니다.")

        # 부산 접두어 제거
        parts.pop(0)

        with self.engine as conn:
            # 후보 리스트 조회
            gu_list = [r[0] for r in conn.execute(text("SELECT SIG_KOR_NM FROM SIG_CODE")).fetchall()]
            dong_list = [r[0] for r in conn.execute(text("SELECT DISTINCT EMD_KOR_NM FROM EMD_CODE")).fetchall()]

            # 접두어 매칭 함수
            def complete_part(part, candidates):
                return next((c for c in candidates if c.startswith(part)), part)

            # 2) 구/동 분기
            if len(parts) >= 2:
                gu_input, dong_input = parts[-2], parts[-1]
                gu_name = complete_part(gu_input, gu_list)
                dong_name = complete_part(dong_input, dong_list)

                # 구 조회
                gu = conn.execute(
                    text("SELECT SIG_CD, SIG_KOR_NM FROM SIG_CODE WHERE SIG_KOR_NM = :gu"),
                    {"gu": gu_name}
                ).fetchone()
                if not gu:
                    raise HTTPException(status_code=404, detail="해당 구를 찾을 수 없습니다.")

                sig_cd, sig_nm = gu

                # 동 조회
                dong = conn.execute(
                    text("""
                        SELECT EMD_CD, EMD_KOR_NM FROM EMD_CODE
                        WHERE EMD_KOR_NM = :dong AND LEFT(EMD_CD, 5) = :sig_cd
                    """),
                    {"dong": dong_name, "sig_cd": sig_cd}
                ).fetchone()
                if not dong:
                    raise HTTPException(status_code=404, detail="해당 동을 찾을 수 없습니다.")

                return {
                    "level": "동",
                    "code": dong[0],
                    "matched_name": f"{sig_nm} {dong[1]}"
                }

            else:  # parts == 1 → 구만 입력
                gu_input = parts[0]
                gu_name = complete_part(gu_input, gu_list)
                gu = conn.execute(
                    text("SELECT SIG_CD, SIG_KOR_NM FROM SIG_CODE WHERE SIG_KOR_NM = :gu"),
                    {"gu": gu_name}
                ).fetchone()
                if not gu:
                    raise HTTPException(status_code=404, detail="해당 구를 찾을 수 없습니다.")
                sig_cd, sig_nm = gu
                return {
                    "level": "구",
                    "code": sig_cd,
                    "matched_name": sig_nm
                }
