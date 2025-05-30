from shapely import wkt
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import transform
from pyproj import Transformer

class GeometryParser:
    def __init__(self):
        self.transformer_5179 = Transformer.from_crs("EPSG:5179", "EPSG:4326", always_xy=True)
        self.transformer_5181 = Transformer.from_crs("EPSG:5181", "EPSG:4326", always_xy=True)
        self.transformer_5186 = Transformer.from_crs("EPSG:5186", "EPSG:4326", always_xy=True)

    def parse_geometry_to_list(self, geometry: str, level: str) -> list:
        polygon = wkt.loads(geometry)
        # level에 따라 변환 EPSG를 실험적으로 바꿔보세요
        if level == "동":
            polygon = transform(self.transformer_5179.transform, polygon)
        else:  # level == "구"
            # EPSG:5186로 변환
            polygon = transform(self.transformer_5186.transform, polygon)
        if isinstance(polygon, MultiPolygon):
            polygons = list(polygon.geoms)
        else:
            polygons = [polygon]
        result = []
        for poly in polygons:
            if isinstance(poly, Polygon):
                coords = list(poly.exterior.coords)
                result.append([{"lat": y, "lng": x} for x, y in coords])
        return result
