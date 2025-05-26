import pandas as pd
from sqlalchemy import (
    create_engine, MetaData, Table,
    Column, Integer, String, CHAR, text
)
from sqlalchemy.dialects.mysql import REAL

df = pd.read_csv("smart_bus_station.csv")


HOST     = "127.0.0.1"
PORT     = 3306
USER     = "root"
PASSWORD = "600900"
DB_NAME  = "bus_db"

db_connection = create_engine(
    f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"
)

with db_connection.begin() as conn:
    conn.execute(text("DROP TABLE IF EXISTS smart_bus_station;"))

metadata = MetaData()

bus_table = Table(
    "smart_bus_station", metadata,
    Column("id",            Integer, primary_key=True, autoincrement=True),
    Column("sgg_code",      String(20), nullable=True),
    Column("umd_code",      String(20), nullable=True),
    Column("sgg_name",      String(10),nullable=True),
    Column("umd_name",      String(10),nullable=True),
    Column("station_name",  String(30),nullable=True),
    Column("line_num",      String(150),nullable=True),
    Column("arsno",         String(10), nullable=True),
    Column("lat",           REAL,      nullable=True),
    Column("lon",           REAL,      nullable=True),
    Column("score",         REAL,       nullable=True),   
    Column("rank",          CHAR(1),  nullable=True),
)


metadata.create_all(db_connection)

df.to_sql(
    name="smart_bus_station",
    con=db_connection,
    if_exists="append",
    index=False,
    dtype={
        "sgg_code":     String(20),
        "umd_code":     String(20),
        "sgg_name":     String(10),
        "umd_name":     String(10),
        "station_name": String(30),
        "line_num":     String(150),
        "arsno":        String(10),
        "lat":          REAL,
        "lon":          REAL,
        "score":        REAL,
        "rank":         CHAR(1),
    }
)

print("smart_bus_station 테이블에 데이터 업로드 완료")
