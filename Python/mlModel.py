from Python.getData import *
from Python.BBox import Bbox
import numpy as np
from sklearn.model_selection import train_test_split
from Python.downloadCompositeImage import composite_image
import os
import pandas as pd
from rasterio import features
from rasterio.enums import Resampling
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score
import joblib
from shapely.geometry import shape

class Model:
    """
    A class to train and/or use a Machine Learning model to predict pixels that contain developed area based on satelite imagery
    """
    def __init__(self, year, bbox: Bbox, train_area=None):
        """
        Initialize the model.
        
        Args:
            year (int): Year for which you want a prediction
            bbox (shapely.geometry.Polygon): Boundary box for the area you want to predict
            train_area (str): Path to shapefile that stores your training area (optional)
        """
        self.train_area = train_area
        self.sat_path = "Data/Train/train_data.tif"
        self.class_path = "Data/Train/classifiedRaster.tif"
        self.model_path = "Data/Train/knn_model.pkl"
        self.townName = bbox.name.replace(" ", "_")
        self.year = year
        self.bbox = bbox
        self.bounds_cr = "Data/boundaries_cr.shp"
        self.shapefile_path = f"Data/{self.townName}/Processed/{self.townName}_{self.year}.shp".replace(" ", "_")
        return

    def get_train_bounds(self):
        """
        Initialize training bounds using the train area provided
        """
        if self.train_area:
            gdf = gpd.read_file(self.train_area)
            self.trainbounds = gdf.total_bounds.tolist()
        return
    

    def prepare_data(self):
        """
        Prepare data for training a new model, get the boundaries and download corresponding satellite and classified data
        
        Returns:
            X (np.ndarray), and y (np.ndarray)
        """
        self.get_train_bounds()
        if os.path.exists(self.sat_path):
            with rasterio.open(self.sat_path) as src:
                self.sat_data = src.read()  # (bands, height, width)
        else:
            self.sat_data = composite_image(self.trainbounds, year=2021)
            with rasterio.open(self.sat_path) as src:
                self.sat_data = src.read()

        if os.path.exists(self.class_path):
            with rasterio.open(self.class_path) as src:
                self.label_data = src.read(1)
        else:
            self.label_data = getCoverData(self.trainbounds)
            with rasterio.open(self.label_data) as src:
                self.label_data = src.read(1)

        self.sat_data = self.crop_to_label_extent(self.sat_path, self.class_path)

        self.label_data = self.resample_labels(self.class_path, self.sat_data.shape[1:])

        # --- Flatten for ML ---
        X = self.flatten_data(self.sat_data)
        y = self.label_data.flatten()

        return X, y

    def flatten_data(self, data):
        """
        Flatten data to an 1 dimensional form for training a model
        """
        n_bands = data.shape[0]
        return np.stack([data[i].flatten() for i in range(n_bands)], axis=1)

    def crop_to_label_extent(self, sat_path, label_path):
        """
        Crop satellite raster to the bounds of the label raster, handling CRS differences.
        
        Returns:
            sat_data_cropped (np.ndarray): Cropped satellite data (bands, height, width)
        """
        with rasterio.open(sat_path) as sat_src, rasterio.open(label_path) as lbl_src:
            # Transform label bounds to satellite CRS
            lbl_bounds_in_sat_crs = transform_bounds(
                lbl_src.crs, sat_src.crs, *lbl_src.bounds
            )

            # Create window in satellite raster
            window = from_bounds(*lbl_bounds_in_sat_crs, transform=sat_src.transform)

            # Read cropped satellite data
            sat_data_cropped = sat_src.read(window=window)

        return sat_data_cropped
    
    
    def resample_labels(self, label_path, target_shape):
        """
        Resample label raster to match a target shape (height, width).
        
        Args:
            label_path (str): Path to label raster
            target_shape (tuple): (height, width) of the target raster
        
        Returns:
            resampled_labels (np.ndarray): Resampled label array
        """
        target_height, target_width = target_shape
        with rasterio.open(label_path) as src:
            resampled_labels = src.read(
                1,
                out_shape=(target_height, target_width),
                resampling=Resampling.nearest
            )
        return resampled_labels


    def split_train_val_test(self):
        """
        Split data in training, validation and testing sets
        """
        X, y = self.prepare_data()
        # Split training and test data 80 to 20, and split the training data further for validation 60 to 20
        X_train, self.X_test, y_train, self.y_test = train_test_split(X, y, test_size=0.2, random_state=1)

        self.X_train, self.X_val, self.y_train, self.y_val = train_test_split(X_train, y_train, test_size=0.25, random_state=1)
        print("Data succesfully split")
        return 



    def init_knn_model(self, n_neighbors=10):
        """
        Initialize a KNN model and save it to a data folder for later use

        Args:
            n_neighbors (int): Specify the amount of neighbors to use in the knn model
        """
        self.split_train_val_test()
        train_accuracies = []
        val_accuracies = []
        knn = KNeighborsClassifier(n_neighbors=n_neighbors)
        knn.fit(self.X_train, self.y_train)

        train_accuracy = accuracy_score(self.y_train, knn.predict(self.X_train))
        test_accuracy = accuracy_score(self.y_val, knn.predict(self.X_val))

        # Store results
        train_accuracies.append(train_accuracy)
        val_accuracies.append(test_accuracy)

        print(f"n_neighbors={n_neighbors}, train_accuracy={train_accuracy:.4f}, test_accuracy={test_accuracy:.4f}")
        joblib.dump(knn, self.model_path)
        print("Model saved to knn_model.pkl")
        return

    def run_model(self):
        """
        Function that predicts most likely class for each pixel of a raster
        - Saves a raster with each pixel the predicted class based on WorldCover_PUM_v1.0
        - Saves a polygon with only the developed areas excluding pixels that were outside the borders of Costa Rica
        """
        if not os.path.exists(self.model_path):
            if not self.train_area:
                return print("No training area provided and no existing model found")
            self.init_knn_model()
            
        # Save prediction as GeoTIFF
        output_path = f"Data/{self.townName}/Processed/{self.townName}_{self.year}_pred.tif".replace(" ", "_")
        if not os.path.exists(output_path):
            pred = self.predict()
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with rasterio.open(f"Data/{self.townName}/Base/{self.townName}_{self.year}_base.tif") as src:
                profile = src.profile

            # Update metadata for classification output
            profile.update(
                count=1,                # Single-band classification output
                dtype=rasterio.uint8,   # Supports values 0–255
                nodata=255,             # Reserve 255 as "no data"
                compress='lzw',
                driver='GTiff'
            )
            
            with rasterio.open(output_path, 'w', **profile) as dst:
                dst.write(pred.astype(rasterio.uint8), 1)
        
        if os.path.exists(self.shapefile_path):
            return True
        gdf = self.convert_to_shape(output_path)

        gdf.to_file(self.shapefile_path, driver='ESRI Shapefile')
        print(f"Polygon shapefile developed area saved to: {self.shapefile_path}")

        return False
    
    def convert_to_shape(self, path):
        """
        Converts raster with predicted classes into shapefile with only class value 50 (developed areas)
        
        Returns:
            gdf (GeoDataFrame): geopandas dataframe for the developed area
        """
        with rasterio.open(path) as src:
            mask = src.read(1)
            transform = src.transform
            crs = src.crs

        # Only keep pixels with class value 50
        mask_50 = np.where(mask == 50, 1, 0).astype(np.uint8)

        # Extract shapes (polygons)
        shapes_gen = features.shapes(mask_50, mask=mask_50 == 1, transform=transform)

        # Convert to GeoDataFrame
        polygons = []
        for geom, val in shapes_gen:
            if val == 1:
                polygons.append(shape(geom))

        gdf = gpd.GeoDataFrame(geometry=polygons, crs=crs)

        gdf = self.clip_to_cr(gdf)

        last_shp = f"Data/{self.townName}/Processed/{self.townName}_{self.year-1}.shp"
        if os.path.exists(last_shp):
            last_gdf = gpd.read_file(last_shp)
            gdf = self.merge_shapes(gdf, last_gdf)
        
        return gdf

    def merge_shapes(self, gdf, last_gdf):
        """
        Function to merge and dissolve two shapefiles
        """
        merged = gpd.GeoDataFrame(pd.concat([gdf, last_gdf], ignore_index=True))
        dissolved = merged.dissolve()
        return dissolved

    def clip_to_cr(self, gdf):
        """
        Function to clip a geopandas dataframe to the boundaries of Costa Rica
        """
        gdf_bound = gpd.read_file(self.bounds_cr).to_crs(gdf.crs)  
        gdf = gpd.clip(gdf, gdf_bound)        
        return gdf
    
    def predict(self):
        """
        Function to predict classes for each pixel in a raster based on an existing model
        
        Returns:
            Raster with values corresponding to the predicted class
        """
        knn = joblib.load("Data/knn_model.pkl")
        X_data =  self.import_data(self.townName, self.year)
        
        y_pred = knn.predict(X_data)

        height, width = self.data.shape[1:]

        y_pred_2d = y_pred.reshape(height, width)

        return y_pred_2d


    def import_data(self, townName, year):
        """
        Function that imports satellite data following a specified structure
        """

        path = f"Data/{townName}/Base/{townName}_{year}_base.tif".replace(" ", "_")
        if not os.path.exists(path):
            composite_image(self.bbox, year)
        with rasterio.open(path) as src:
            self.data = src.read()
        X = self.flatten_data(self.data)
        return X
    
