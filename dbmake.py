#sig_code.csv, emd_cod.csv, 행정구역별_위경도_좌표.csv, sgg.gpkg, umd.gpkg 파일 db에 table create 후 insert

from sqlalchemy import create_engine, text
from sqlalchemy.types import Text
import pandas as pd
import geopandas as gpd
import pymysql

# MySQL 연결 설정
DB_NAME = "bus_db"
DB_USER = "root"
DB_PASSWORD = "2204"
DB_HOST = "localhost"
DB_PORT = 3306

engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# 테이블 존재 시 삭제 함수
def recreate_table(table_name):
    with engine.connect() as conn:
        result = conn.execute(text(f"SHOW TABLES LIKE :t"), {"t": table_name}).fetchone()
        if result:
            print(f"🗑 기존 테이블 삭제: {table_name}")
            conn.execute(text(f"DROP TABLE {table_name}"))
        else:
            print(f"✅ 새로 생성할 테이블: {table_name}")

# 파일 경로
sig_path = "SIG_CODE.csv"
emd_path = "EMD_CODE.csv"
coords_path = "행정구역별_위경도_좌표.csv"
sgg_path = "sgg.gpkg"
umd_path = "umd.gpkg"

# sig_code
sig_df = pd.read_csv(sig_path, dtype=str)
sig_df.columns = ["SIG_CD", "SIG_ENG_NM", "SIG_KOR_NM"]
recreate_table("sig_code")
sig_df.to_sql("sig_code", con=engine, if_exists="replace", index=False)

# sgg
sgg_gdf = gpd.read_file(sgg_path)
sgg_gdf["geometry"] = sgg_gdf["geometry"].apply(lambda g: g.wkt)
recreate_table("sgg")
sgg_gdf.to_sql(
    "sgg",
    con=engine,
    if_exists="replace",
    index=False,
    dtype={"geometry": Text(length=4294967295)}
)

# umd
umd_gdf = gpd.read_file(umd_path)
umd_gdf["geometry"] = umd_gdf["geometry"].apply(lambda g: g.wkt)
recreate_table("umd")
umd_gdf.to_sql(
    "umd",
    con=engine,
    if_exists="replace",
    index=False,
    dtype={"geometry": Text(length=4294967295)}
)

# emd_code + umd + sgg 조인
emd_df = pd.read_csv(emd_path, dtype=str)
emd_df.columns = ["EMD_CD", "EMD_ENG_NM", "EMD_KOR_NM"]
umd_cols = gpd.read_file(umd_path)[["EMD_CD", "SGG_OID", "COL_ADM_SE"]].astype(str)
sgg_cols = gpd.read_file(sgg_path)[["SGG_OID", "SGG_NM", "ADM_SECT_C"]].astype(str)

emd_df = emd_df.merge(umd_cols, on="EMD_CD", how="left")
emd_df = emd_df.merge(sgg_cols, on="SGG_OID", how="left")

recreate_table("emd_code")
emd_df.to_sql("emd_code", con=engine, if_exists="replace", index=False)

# coords
coords_df = pd.read_csv(coords_path)
coords_df.columns = ["sido_nm", "sig_nm", "emd_nm", "latitude", "longitude"]
recreate_table("coords")
coords_df.to_sql("coords", con=engine, if_exists="replace", index=False)

print("✅ 모든 테이블 생성 및 데이터 적재 완료")
