from pyproj import Transformer
import geopandas as gpd
from shapely.geometry import Point

class Bbox:
    """
    A class to define a location with coordinate conversion and boundary box generation.
    
    Attributes:
        name (str): Name of the town/location
        x_coord (float): X coordinate (longitude or easting)
        y_coord (float): Y coordinate (latitude or northing)
        wgs84_coords (tuple): Converted coordinates in WGS84 (latitude, longitude)
        bbox (shapely.geometry.Polygon): Boundary box of 5km x 5km around the location
    """
    
    def __init__(self, name_town, coords):
        """
        Initialize a BBox instance.
        
        Args:
            name_town (str): Name of the town/location
            coords (list): [x_coord, y_coord] - coordinates from Google Maps
            input_crs (str): Input coordinate reference system (default: "EPSG:4326" for WGS84)
                            Common options: "EPSG:4326" (WGS84), "EPSG:3857" (Web Mercator),
                            "EPSG:28992" (Dutch RD), etc.
        """

        self.name = name_town

        # Coords are already in epsg 4326 no coversion needed
        self.coords = coords

        # Create 5km x 5km boundary box
        self._create_bbox()
    

    def _create_bbox(self):
        """
        Create a boundary box around the location using Buffer
        """
        pt = Point(self.coords[1], self.coords[0])

        gdf = gpd.GeoDataFrame({'geometry': [pt]}, crs="EPSG:4326")  # WGS84

        gdf_utm = gdf.to_crs("EPSG:32616")

        gdf_utm['geometry'] = gdf_utm.geometry.buffer(5000)

        gdf_buffer_wgs84 = gdf_utm.to_crs("EPSG:4326")

        self.bounds = gdf_buffer_wgs84.total_bounds.tolist()
        
        return self.bounds



# Original coordinates (lon, lat)

