import geopandas as gpd
from openeo.processes import if_, is_nan
from Python.utils_BAP import (calculate_cloud_mask, calculate_cloud_coverage_score,
                           calculate_date_score, calculate_distance_to_cloud_score,
                           calculate_distance_to_cloud_score, aggregate_BAP_scores,
                           create_rank_mask)
import openeo
import numpy as np
from Python.BBox import Bbox
from pathlib import Path
from shapely.geometry import box
import shutil


def composite_image(bbox:Bbox, year: int):
    """" 
    Single function that downloads a composite image for a given year based on Francini et al.'s (2023) algorithm.
        Note: Authentication is required to access Copernicus satellite data,
            the terminal will prompt you the link to sign up and login.

        Functions: Implements function from utils_BAP

        Exports: GTiff raster file of given year with 10 bands of satellite data. 
    """
    # Creating a GeoJson object from the bbox object
    bounds = list(bbox.bounds)       
    xmin, ymin, xmax, ymax = bounds
    area ={
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [xmin, ymin],      # Bottom-left
                        [xmin, ymax],      # Top-left
                        [xmax, ymax],      # Top-right
                        [xmax, ymin],      # Bottom-right
                        [xmin, ymin]       # Close the polygon
                    ]]}}]}

    # Defining parameters (You can play around with these parameters too!)
    temporal_extent = [f"{year}-01-01", f"{year}-03-30"]
    max_cloud_cover = 20
    spatial_resolution = 20
    bands = ["B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B11", "B12"]

    ###
    # Initializing
    ###
    c=openeo.connect("openeo.dataspace.copernicus.eu").authenticate_oidc()

    # Load SCL or cloud band
    scl = c.load_collection(
        "SENTINEL2_L2A",
        temporal_extent=temporal_extent,
        bands=["SCL"],
        max_cloud_cover=max_cloud_cover
    ).resample_spatial(spatial_resolution).filter_spatial(area) 

    # Give NAN values a 0 value
    scl = scl.apply(lambda x: if_(is_nan(x), 0, x))

    # Create a binary cloud mask, which gives 1 if a pixel is classified as cloud by SCL, an 0 otherwise.
    cloud_mask =  calculate_cloud_mask(scl)

    # Calculating coverage score
    coverage_score = calculate_cloud_coverage_score(cloud_mask, area, scl)

    # Calcualting date score
    date_score = calculate_date_score(scl)

    # Calculating istance to cloud source
    dtc_score = calculate_distance_to_cloud_score(cloud_mask, spatial_resolution)

    # Agregating scores based on weights
    weights = [1, 0.8, 0.5]
    score = aggregate_BAP_scores(dtc_score, date_score, coverage_score, weights)
    score = score.mask(scl.band("SCL") == 0)

    # Mask the scores on 
    rank_mask = create_rank_mask(score)

    ###
    # Compositing 
    ###

    bands = c.load_collection(
        "SENTINEL2_L2A",
        temporal_extent = temporal_extent,
        bands = bands,         
        max_cloud_cover=max_cloud_cover
    ).filter_spatial(area)


    composite = bands.mask(rank_mask).mask(cloud_mask).aggregate_temporal_period("month","median")

    ### 
    # Downloading
    ###

    # Main data directories
    town_name = bbox.name.replace(" ", "_")
    output_path = Path("Data") / town_name / "Base"
    output_path.mkdir(parents=True, exist_ok=True)
    file_output = output_path / f"{town_name}_{year}_base.tif"

    # Temporary directories
    temp_dir = output_path / "temp"
    temp_dir.mkdir(exist_ok=True)
    
    
    
    # Executing job
    job = composite.execute_batch(
        title="BAP Composite",
        out_format="GTiff"   
    )
    results = job.get_results()
    results.download_files(str(temp_dir))

    for file in temp_dir.glob("*.tif"):
        shutil.move(str(file), str(file_output))
        break

    # Clean up temp
    shutil.rmtree(temp_dir)

    return None
