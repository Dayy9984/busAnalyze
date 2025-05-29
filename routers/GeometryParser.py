
from shapely import wkt
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import transform
from pyproj import Transformer

class GeometryParser:
    def __init__(self):
        self.transformer = Transformer.from_crs("EPSG:5179", "EPSG:4326", always_xy=True)

    def parse_geometry_to_list(self,geometry: str)->list:
        # 1. WKT �� Shapely ��ü
        polygon = wkt.loads(geometry)
        # 2. ��ǥ�� ��ȯ
        transformed_polygon = transform(self.transformer.transform, polygon)
        # 3. Polygon/MultiPolygon ó��
        if isinstance(transformed_polygon, MultiPolygon):
            polygons = list(transformed_polygon.geoms)
        else:
            polygons = [transformed_polygon]
        # 4. [ {lat, lng}, ... ] �迭�� ��ȯ
        result = []
        for poly in polygons:
            if isinstance(poly, Polygon):
                coords = list(poly.exterior.coords)
                result.append([{"lat": y, "lng": x} for x, y in coords])
        return result
