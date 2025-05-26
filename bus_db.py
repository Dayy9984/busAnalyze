import pandas as pd
from sqlalchemy import (
    create_engine, MetaData, Table,
    Column, Integer, String, CHAR, text
)
from sqlalchemy.dialects.mysql import REAL

df = pd.read_csv("ranked_filtered_scaled_with_codes.csv")


HOST     = "localhost"
PORT     = 3306
USER     = "root"
PASSWORD = "1234"
DB_NAME  = "bus_db"

db_connection = create_engine(
    f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"
)

with db_connection.begin() as conn:
    conn.execute(text("DROP TABLE IF EXISTS bus_blind_spot_ranked;"))

metadata = MetaData()

bus_table = Table(
    "bus_blind_spot_ranked", metadata,
    Column("id",            Integer, primary_key=True, autoincrement=True),
    Column("sgg_code",      String(20), nullable=True),
    Column("sgg_name",      String(10),nullable=True),
    Column("umd_code",      String(20), nullable=True),
    Column("umd_name",      String(10),nullable=True),
    Column("geometry",      String(300),nullable=True),
    Column("lat",           REAL,      nullable=True),
    Column("lon",           REAL,      nullable=True),
    Column("score",         REAL,       nullable=True),   
    Column("rank",          CHAR(1),  nullable=True),
)


metadata.create_all(db_connection)

df.to_sql(
    name="bus_blind_spot_ranked",
    con=db_connection,
    if_exists="append",
    index=False,
    dtype={
        "sgg_code":     String(20),
        "sgg_name":     String(10),
        "umd_code":     String(20),
        "umd_name":     String(10),
        "geometry":     String(300),
        "lat":          REAL,
        "lon":          REAL,
        "score":        REAL,
        "rank":         CHAR(1),
    }
)

print("bus_blind_spot_ranked 테이블에 데이터 업로드 완료")
