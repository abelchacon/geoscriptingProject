#Cuddly kaas en cunning tomaat
#Geoscripting 2025 Final Project
#Script for downloading data 

#import packages
from Python.BBox import Bbox 
import geopandas as gpd
import rasterio
from pystac_client import Client
from planetary_computer import sign
import zipfile
import matplotlib.pyplot as plt
import os

"""Function for downloading protected areas vector file
& clipping it to the extent of the previously
defined boundary box"""
def download_protected(bbox: Bbox):
    protected_path = "Data/Geodata_CR/AreasProtegidasWGS84.shp"
    if not os.path.exists(protected_path):
        #extract zip file
        protected_zip = "Data/Geodata_CR/AreasProtegidas.zip"
        with zipfile.ZipFile(protected_zip, 'r') as zip_ref:
            zip_ref.extractall('./Data/Geodata_CR')
    return 


def getCoverData (bbox: Bbox):
    """Function that downloads world cover data based on a specified bounding box, 
    it returns the file path and saves it as a .tif file"""
    catalog = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")
    search = catalog.search(
    collections=["esa-worldcover"],
    bbox=bbox.bounds,
    datetime="2021-01-01/2021-12-31"
    )
    item = next(search.items())

    signed_item = sign(item)
    href = signed_item.assets["map"].href


    output_path = "Data/Train/classifiedRaster.tif"
    with rasterio.open(href) as src:
        # Compute window covering bbox
        window = rasterio.windows.from_bounds(*bbox.bounds, transform=src.transform)
        
        # Read data in that window
        data = src.read(1, window=window)
        
        # Calculate the transform for the windowed subset
        transform = src.window_transform(window)
        
        # Define output metadata
        profile = src.profile
        profile.update({
            "height": data.shape[0],
            "width": data.shape[1],
            "transform": transform,
            "driver": "GTiff"
        })
        
        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(data, 1)
    
    return output_path

