from fastapi import APIRouter, HTTPException, Depends
from dbmodule import dbmodule
import pandas as pd
import datetime

router = APIRouter(
    prefix="/api",
    tags=["test"]
)
db = dbmodule()

@router.get("/get_delivery")
def get_delivery(category: str):
    sorted_categories = [
        '고기구이','버거','분식','샌드위치','찜탕',
        '치킨','카페디저트','피자양식','한식','회초밥',
        '아시안','야식','일식돈까스','족발보쌈','중식'
    ]
    mapping = {
        '고기구이':'고기/구이','카페디저트':'카페/디저트',
        '피자양식':'피자/양식','회초밥':'회/초밥',
        '일식돈까스':'일식/돈까스','족발보쌈':'족발/보쌈'
    }

    engine = db.get_db_con('delivery')
    df = pd.read_sql("SELECT * FROM delivery_data", con=engine)

    now = str(df['time'].max())
    prev = (datetime.datetime.strptime(now, '%Y%m%d_%H')
            - datetime.timedelta(hours=1)).strftime('%Y%m%d_%H')

    curr_df = df[df['time']==now]
    past_df = df[df['time']==prev]

    diffs = {
        c: curr_df[curr_df[c]==1]['adjusted_delivery_fee'].mean()
           - past_df[past_df[c]==1]['adjusted_delivery_fee'].mean()
        for c in sorted_categories
    }
    min_cat = mapping.get(min(diffs, key=diffs.get), min(diffs, key=diffs.get))

    cat_df = df[df[category]==1].groupby('time')['adjusted_delivery_fee']\
                .mean().reset_index(name='avg_fee')
    pct = cat_df['avg_fee'].pct_change().fillna(0) * 100
    cat_df['diff_pct'] = pct

    return {
        'min_diff_category': min_cat,
        'category_time_avg': dict(zip(cat_df['time'], cat_df['avg_fee'])),
        'category_diff_percentage': dict(zip(cat_df['time'], cat_df['diff_pct']))
    }
