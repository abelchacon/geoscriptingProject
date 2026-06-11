from Python.BBox import Bbox
from Python.downloadCompositeImage import composite_image
from Python.statisticsPlotter import save_stats
from Python.plotGraphs import *
from Python.downloadData import *
from Python.mlModel import Model
from Python.checkProtectedAreas import check_build_protected

# Define your town data (these are the towns for which we already provided the data and the predictions)
towns = {
    "Tamarindo": [10.295710, -85.840380],
    "Puerto Viejo": [9.654632, -82.750544],
    "Santa Teresa": [9.643742, -85.166511],
    "Uvita": [9.163817, -83.739108],
    "Coco": [10.54885, -85.69652],
}

# Create Bbox objects using a dict comprehension
bboxes = {name: Bbox(name, coords) for name, coords in towns.items()}

# Define year range
years = range(2016, 2026)  # 2016 to 2025 inclusive (2015 fails in all towns due to low quality satellite images before 2016)

#run classification model on the dataset
for name, bbox in bboxes.items():
    for year in years:
        try:
            print(f"Processing {name} for year {year}...")
            ml = Model(year, bbox)
            status = ml.run_model()
            if status is True:
                print(f"Shapefile was already created, no further processing is needed for {name} - {year}")
            else:
                print(f"Successfully processed {name} - {year}")
        except Exception as e:
            error_msg = f"{name} - {year}: {str(e)}"
            print(f"Error: {error_msg}")
            continue


# Save the statistics for each town and an overall comparison between the towns in the dataset
save_stats(towns, years)

# Check if the model predicted building activity in protected areas in Costa Rica
for name in towns.keys():
    if check_build_protected(name) is True:
        print(f"The model predicted that there was build inside of protected areas close to {name}, for more information see the output file")
    else:
        print(f"No build activity was predicted in protected areas close to {name}")

# This creates a plot showing the development over the years for the town Tamarindo
animated_plot(bboxes["Tamarindo"], list(years), buffer_percent=-10)


########################################################################################
### Extra code examples
########################################################################################

## If you want to plot and save the development for a certain town for one specific year 
# year_plot(bboxes["Uvita"], 2018)

# # Code example to download the satellite imagery for a town (normally this is included in running the model)
# bbox = Bbox("Samara", [9.88159, -85.53183])
# # Specify a bbox and a year, the image will be saved in the Data folder in a folder with a corresponding name
# composite_image(bbox, 2021)

# # Code example if you want to train a new model based on your own training area
# import geopandas as gpd
# train_area = gpd.read_file("path/to/your/training/area")
# ml = Model(2021, bbox, train_area=train_area)

## Example for a town to test the downloading functions
## Keep in mind that downloading the data and making predictions can take around an hour
# new_towns = {
#     "Samara": [9.88159, -85.53183],
# }

## Create Bbox objects using a dict comprehension
# new_bboxes = {name: Bbox(name, coords) for name, coords in new_towns.items()}

## Define year range
# years = range(2020, 2026)  

# #run classification model on the dataset
# for name, bbox in new_bboxes.items():
#     for year in years:
#         try:
#             print(f"Processing {name} for year {year}...")
#             ml = Model(year, bbox)
#             status = ml.run_model()
#             if status is True:
#                 print(f"Shapefile was already created, no further processing is needed for {name} - {year}")
#             else:
#                 print(f"Successfully processed {name} - {year}")
#         except Exception as e:
#             error_msg = f"{name} - {year}: {str(e)}"
#             print(f"Error: {error_msg}")
#             continue
