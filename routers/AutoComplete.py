import re
from fastapi import APIRouter, Query, HTTPException
from sqlalchemy import text
from dbmodule import dbmodule

router = APIRouter()
DB_NAME = "bus_db"

@router.get("/backend/autocomplete")
def autocomplete(address: str = Query(..., alias="address", min_length=1)):
    cleaned = re.sub(r'^(부산(광역시)?\s*)', '', address.strip())
    if not cleaned:
        raise HTTPException(status_code=400, detail="검색어를 입력하세요.")
    
    pattern = f"%{cleaned}%"

    db = dbmodule()
    engine = db.get_db_con(DB_NAME)

    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT DISTINCT
                CONCAT(s.SIG_KOR_NM, ' ', e.EMD_KOR_NM) AS full_name
            FROM emd_code AS e
            JOIN sig_code AS s
              ON LEFT(e.EMD_CD, 5) = s.SIG_CD
            WHERE CONCAT(s.SIG_KOR_NM, ' ', e.EMD_KOR_NM) LIKE :pattern
            ORDER BY full_name
            LIMIT 10
        """), {"pattern": pattern}).mappings().all()

    return [r["full_name"] for r in rows]
