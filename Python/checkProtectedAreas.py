import geopandas as gpd
import pandas as pd
import geopandas as gpd
import pandas as pd
from pathlib import Path

def check_build_protected(name):
    """
    Checks if for a certain town there was build in protected areas in Costa Rica
    
    Args:
        name: give the townname
    """
    town_path = Path(f"Data/{name}/Processed/{name}_2025.shp".replace(" ", "_"))
    output_folder = Path(f"Output/{name}")
    # Load shapefiles
    protected_area = gpd.read_file("Data/Geodata_CR/AreasProtegidasWGS84.shp")
    town_area = gpd.read_file(town_path)

    # Ensure same CRS
    if protected_area.crs != town_area.crs:
        town_area = town_area.to_crs(protected_area.crs)

    # Fix invalid geometries and explode MultiPolygons
    protected_area = protected_area.explode(ignore_index=True)
    town_area = town_area.explode(ignore_index=True)

    protected_area["geometry"] = protected_area.buffer(0)  # repair invalid geometries if needed
    town_area["geometry"] = town_area.buffer(0)

    # Merge all protected areas into a single geometry
    protected_union = protected_area.union_all()

    # Convert the union geometry back into a GeoDataFrame
    protected_union_gdf = gpd.GeoDataFrame(geometry=[protected_union], crs=protected_area.crs)

    inside = gpd.overlay(town_area, protected_union_gdf, how="intersection")
    inside["illegal"] = True

    outside = gpd.overlay(town_area, protected_union_gdf, how="difference")
    outside["illegal"] = False

    # Combine back
    split = pd.concat([inside, outside], ignore_index=True)
    split_gdf = gpd.GeoDataFrame(split, crs=town_area.crs)

    # Dissolve by overlap to make one polygon per True/False
    dissolved = split_gdf.dissolve(by="illegal")

    # Reset index so overlap becomes a column again
    dissolved = dissolved.reset_index()

    # Save result
    output_folder.mkdir(parents=True, exist_ok=True)

    output_path = Path(output_folder, town_path.stem + "_protected.shp")
    dissolved.to_file(output_path, driver="ESRI Shapefile")

    print(f"Saved shapefile to {output_path}")
    has_overlap = not inside.empty
    return has_overlap

