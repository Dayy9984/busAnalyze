'''파일 경로 및 GPKG 설정 (필수!!!):

BASE_DIR: CSV 파일들이 위치한 디렉토리 경로로 수정해주세요.
GPKG_FILE_PATH: 실제 GPKG 파일의 전체 경로로 수정해주세요.
GPKG_LAYER_NAME: GPKG 파일 내에 여러 레이어가 있다면, 사용할 특정 레이어 이름을 지정해야 할 수 있습니다. 단일 레이어라면 None으로 두거나 생략해도 geopandas가 알아서 읽을 수 있습니다.
GPKG_SIG_CODE_COL, GPKG_EMD_CODE_COL: GPKG 파일 내에서 시군구 코드와 읍면동 코드를 담고 있는 실제 컬럼 이름으로 반드시 변경해야 합니다. 이 코드가 없으면 경계 데이터를 CSV의 코드와 연결할 수 없습니다.
데이터 로딩 시점: 위 코드는 FastAPI 애플리케이션이 처음 시작될 때 전역 변수 sig_df, emd_df, coords_df, boundaries_gdf에 데이터를 로드합니다. 이는 매 요청마다 파일을 읽는 것보다 훨씬 효율적입니다. 
try-except 블록으로 파일 로드 실패 시를 대비했지만, 실제 운영 환경에서는 로깅 및 에러 처리를 더 견고하게 해야 합니다.

parse_geometry_to_list 함수 변경:

입력이 WKT 문자열이 아니라 geopandas가 읽어 들인 shapely.geometry 객체이므로, 함수 내부에서 wkt.loads()를 호출할 필요가 없습니다. geometry 객체의 속성을 바로 사용하도록 수정했습니다.
MultiPolygon의 경우, 현재 코드는 첫 번째 유효한 하위 폴리곤의 외부 경계만 사용합니다. 모든 부분을 포함하거나 다른 방식으로 처리해야 한다면 이 부분을 수정해야 합니다.
컬럼 이름 일관성:

행정구역별_위경도_좌표.csv 파일의 컬럼명을 코드에서 사용하기 편하도록 EMD_NM_COORDS, LAT_COORDS, LON_COORDS로 변경하여 사용했습니다 (rename 함수). 실제 CSV 파일의 컬럼명과 일치시키거나, 코드의 rename 부분을 조정하세요.
모든 CSV 파일과 GPKG 파일에서 사용되는 코드(SIG_CD, EMD_CD)의 데이터 타입이 문자열(str)로 일관되도록 dtype={'SIG_CD': str} 등을 사용하여 로드하거나, 조회 전에 astype(str)로 변환했습니다. 이는 숫자형 코드 앞에 '0'이 있는 경우(예: '02110') 유실되지 않도록 하기 위함입니다.
검색 로직의 한계:

현재 문자열 검색은 startswith() (부분 문자열이 이름의 시작 부분과 일치)를 사용합니다. "해운대"로 "해운대구"는 찾지만, "운대구"로는 "해운대구"를 찾지 못합니다. 더 유연한 검색(예: 중간 일치)이 필요하면 contains() 등을 사용할 수 있지만, 정확도가 떨어질 수 있습니다.
동일한 검색어로 여러 결과가 나올 경우(예: "중동"이라는 동이 여러 구에 있는 경우), 현재 코드는 대부분 첫 번째 찾은 결과를 사용합니다. 이를 어떻게 처리할지에 대한 정책이 필요할 수 있습니다.

의존성: 이 코드를 실행하려면 pandas, geopandas, shapely 라이브러리가 설치되어 있어야 합니다. (FastAPI, uvicorn은 기본). geopandas는 내부적으로 fiona, pyproj, rtree 등 여러 C 라이브러리에 의존하므로 설치가 다소 까다로울 수 있습니다.
'''

# routers/test.py
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
import pandas as pd
import geopandas as gpd
from shapely import wkt

router = APIRouter()

# === 파일 경로 설정 ===
SGG_GPKG_PATH = "sgg.gpkg"
UMD_GPKG_PATH = "umd.gpkg"
SIG_CODE_CSV = "SIG_CODE.csv"
EMD_CODE_CSV = "EMD_CODE.csv"
COORDS_CSV = "행정구역별_위경도_좌표.csv"

# === 전역 데이터 로딩 ===
try:
    print("📦 데이터 로딩 시작...")
    sig_df = pd.read_csv(SIG_CODE_CSV, dtype={'SIG_CD': str})
    emd_df = pd.read_csv(EMD_CODE_CSV, dtype={'EMD_CD': str})
    emd_df['SIG_CD_derived'] = emd_df['EMD_CD'].str.slice(0, 5)

    coords_df = pd.read_csv(COORDS_CSV)
    coords_df.rename(columns={'읍면동/구': 'EMD_NM_COORDS', '위도': 'LAT_COORDS', '경도': 'LON_COORDS'}, inplace=True)

    sgg_gdf = gpd.read_file(SGG_GPKG_PATH)
    sgg_gdf["SIG_CD"] = sgg_gdf["SIG_CD"].astype(str)

    umd_gdf = gpd.read_file(UMD_GPKG_PATH)
    umd_gdf["EMD_CD"] = umd_gdf["EMD_CD"].astype(str)

    print("✅ 모든 데이터 로드 완료.")
except Exception as e:
    print(f"❌ 데이터 로드 실패: {e}")
    sig_df, emd_df, coords_df = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    sgg_gdf, umd_gdf = gpd.GeoDataFrame(), gpd.GeoDataFrame()


def parse_geometry_to_list(geometry_obj) -> list:
    if not geometry_obj or geometry_obj.is_empty:
        return []
    try:
        if geometry_obj.geom_type == 'Polygon':
            coords = list(geometry_obj.exterior.coords)
        elif geometry_obj.geom_type == 'MultiPolygon':
            coords = []
            for poly in geometry_obj.geoms:
                if not poly.is_empty and poly.exterior:
                    coords = list(poly.exterior.coords)
                    break
        else:
            return []
        return [{"lat": y, "lng": x} for x, y in coords]
    except Exception as e:
        print(f"[!] Geometry 파싱 오류: {e}")
        return []


async def get_coordinates_by_address(address: str) -> dict:
    if sig_df.empty or emd_df.empty or coords_df.empty or sgg_gdf.empty or umd_gdf.empty:
        raise HTTPException(status_code=503, detail="서버 내부 데이터가 준비되지 않았습니다.")

    parts = [p.strip() for p in address.strip().split() if p.strip()]
    if not parts:
        raise HTTPException(status_code=400, detail="유효한 주소 문자열이 필요합니다.")

    lat, lon, geometry, level, name_log = None, None, None, "", address

    # 시나리오 1: 구 + 동
    if len(parts) >= 2:
        gu = parts[-2]
        dong = parts[-1]
        gu_rows = sig_df[sig_df['SIG_KOR_NM'].str.startswith(gu, na=False)]
        for _, gu_row in gu_rows.iterrows():
            sig_cd = gu_row['SIG_CD']
            emd_rows = emd_df[(emd_df['EMD_KOR_NM'].str.startswith(dong, na=False)) & (emd_df['SIG_CD_derived'] == sig_cd)]
            if not emd_rows.empty:
                emd_cd = emd_rows.iloc[0]['EMD_CD']
                gu_name = gu_row['SIG_KOR_NM']
                dong_name = emd_rows.iloc[0]['EMD_KOR_NM']
                coord_row = coords_df[(coords_df['시군구'] == gu_name) & (coords_df['EMD_NM_COORDS'] == dong_name)]
                if not coord_row.empty:
                    bound_row = umd_gdf[umd_gdf["EMD_CD"] == emd_cd]
                    if not bound_row.empty:
                        lat = coord_row.iloc[0]['LAT_COORDS']
                        lon = coord_row.iloc[0]['LON_COORDS']
                        geometry = bound_row.iloc[0]['geometry']
                        level = "동"
                        name_log = f"{gu_name} {dong_name}"
                        break
        if lat: pass

    # 시나리오 2: 동만
    if not lat and len(parts) >= 1:
        dong = parts[-1]
        emd_rows = emd_df[emd_df['EMD_KOR_NM'].str.startswith(dong, na=False)]
        if not emd_rows.empty:
            row = emd_rows.iloc[0]
            emd_cd = row['EMD_CD']
            dong_name = row['EMD_KOR_NM']
            sig_cd = row['SIG_CD_derived']
            sig_row = sig_df[sig_df['SIG_CD'] == sig_cd]
            gu_name = sig_row.iloc[0]['SIG_KOR_NM'] if not sig_row.empty else "알수없는구"
            coord_row = coords_df[(coords_df['시군구'] == gu_name) & (coords_df['EMD_NM_COORDS'] == dong_name)]
            bound_row = umd_gdf[umd_gdf["EMD_CD"] == emd_cd]
            if not coord_row.empty and not bound_row.empty:
                lat = coord_row.iloc[0]['LAT_COORDS']
                lon = coord_row.iloc[0]['LON_COORDS']
                geometry = bound_row.iloc[0]['geometry']
                level = "동"
                name_log = f"{gu_name} {dong_name}"

    # 시나리오 3: 구만
    if not lat and len(parts) >= 1:
        gu = parts[-1]
        gu_rows = sig_df[sig_df['SIG_KOR_NM'].str.startswith(gu, na=False)]
        if not gu_rows.empty:
            sig_cd = gu_rows.iloc[0]['SIG_CD']
            gu_name = gu_rows.iloc[0]['SIG_KOR_NM']
            coord_row = coords_df[(coords_df['시군구'] == gu_name) & ((coords_df['EMD_NM_COORDS'].isna()) | (coords_df['EMD_NM_COORDS'] == ''))]
            bound_row = sgg_gdf[sgg_gdf["SIG_CD"] == sig_cd]
            if not coord_row.empty and not bound_row.empty:
                lat = coord_row.iloc[0]['LAT_COORDS']
                lon = coord_row.iloc[0]['LON_COORDS']
                geometry = bound_row.iloc[0]['geometry']
                level = "구"
                name_log = gu_name

    if not lat or not geometry:
        raise HTTPException(status_code=404, detail=f"'{address}'에 해당하는 지역을 찾을 수 없습니다.")

    polygon_coords = parse_geometry_to_list(geometry)

    return {
        "coordinates": [lon, lat],
        "multiPolygon": polygon_coords,
        "matched_level": level,
        "matched_name": name_log
    }


# ✅ 전체 정보 반환
@router.get("/backend/selected_coordinates")
async def get_coordinates_by_full_response(
    address: str = Query(..., min_length=1)
):
    return await get_coordinates_by_address(address)


# ✅ 네이버 지도 API용 [{lat, lng}, ...]만 반환
@router.get("/backend/naver_polygon")
async def get_naver_map_polygon_only(
    address: str = Query(..., min_length=1)
):
    result = await get_coordinates_by_address(address)
    return JSONResponse(content=result["multiPolygon"])
