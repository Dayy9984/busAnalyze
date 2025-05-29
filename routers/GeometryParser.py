
from shapely import wkt
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import transform
from pyproj import Transformer

class GeometryParser:
    def __init__(self):
        self.transformer = Transformer.from_crs("EPSG:5179", "EPSG:4326", always_xy=True)

    def parse_geometry_to_list(self,geometry: str)->list:
        # 1. WKT → Shapely 객체
        polygon = wkt.loads(geometry)
        # 2. 좌표계 변환
        transformed_polygon = transform(self.transformer.transform, polygon)
        # 3. Polygon/MultiPolygon 처리
        if isinstance(transformed_polygon, MultiPolygon):
            polygons = list(transformed_polygon.geoms)
        else:
            polygons = [transformed_polygon]
        # 4. [ {lat, lng}, ... ] 배열로 변환
        result = []
        for poly in polygons:
            if isinstance(poly, Polygon):
                coords = list(poly.exterior.coords)
                result.append([{"lat": y, "lng": x} for x, y in coords])
        return result
