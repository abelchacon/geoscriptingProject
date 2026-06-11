# Mapping urban development in 4 popular tourist hotspots in Costa Rica from 2016 to 2025

- Title: Mapping urban development in 4 popular tourist hotspots in Costa Rica from 2016 to 2025 
- Team name and members: Cuddly kaas en cunning tomaat (Niels Adriaansen, Abel Chacon, Jingxi Lu, Julia Lewicki)
- Challenge number (or "own"): own

## Background information
Costa Rica is a popular tourist destination for many tourists wanting to enjoy its beautiful nature and pristine beaches, attracting 2,6 million tourists throughout 2024 (ICT). Tourism accounts for 8,2% of Costa Rica's GDP and is most popular around beaches on both Pacific and Carribean coasts. However, this rapid expansion and investment in tourism, particularly foreign investment in real estate comes at a price. Namely through corruption and legal-loopholes, real-estate projects end up building inside of protected areas that protected under the Forestry Law (SJIC). For example, Playa Panama, a pristine beach and tropical-dry forest is being threatened by a megaproject of 130 hectares full of condos, swimming pools and golf courses (Semanario Universidad). 

Being able to visualize the growth of tourist locations around the most popular places can give us insights into the effects of tourism on coastal landscapes and whether this urbanization is infringing in protected areas.

- Temporal extent: 2016-2025
- Frequency: yearly
- Locations: Puerto Viejo, Tamarindo, Santa Teresa, Uvita

## Objective and Research questions
This project uses Sentinel 2 images and a KNN model to classify urbanized areas of popular tourist locations in Costa Rica

- How have the towns Puerto Viejo, Tamarindo, Santa Teresa, and Uvita grown in size?
- Which town has observed most development in a single year? 
- Which town has observed most development from 2016 to 2025?
- Is urban development infringing protected area boundaries in the towns?


## Data
The definition of the towns being studied are defined by a class called Bbox, you can change the towns by defining its name and adding a center point from a map viewer such as Google Maps (in EPSG:4326). Two extra towns are provided (Coco and Samara).
### Case study Data
OpenEO API is used to source the images and uses a Best Available Pixel (BAP) algorithm to mask out cloud cover developed by Francini et al. (2023). 


### Training data
- There is training data available, or you can create your own. The training data should be in a shapefile format and contain a polygon that represent the area being used to train a model
- The bounds of the training polygon will be used to download the corresponding sentinel data and to retrieve the labels from the WorldCover (2021 v200) database.


## Land use classification 
- A KNN model is available for use but you also have the option to train a new model with different arguments or on a different area, currently only the amount of neighbors can be changed for the parameters.
- The model is implemented on case study areas and outputs a raster file with for each pixel the predicted class, and a shapefile that contains only the pixels where developed area is predicted.


## Visualization
- To visualize the outcomes of our training model, we chose to both plot the polygons individually by year and by incorporating an animated plot where you can see the changes in the polygon over time.
- When designing the plots, we took care to make sure the polygon changes were as visible and as visually pleasing as possible.
- Graphs are created showing the percentage growth by year for each town
- Graphs show the highest single year growth of each town and the total percentage growth of each town. 


## Running instructions 
- You can run main the entire pipeline, however it might takes several hours, therefore you can access the base satellite imagery and the urban classified areas through the following link:
 [Download and add to the repo locally](https://wageningenur4.sharepoint.com/:f:/r/sites/course-328650-group/Shared%20Documents/Announcements/Group%20Cuddly%20kaas%20en%20cunning%20tomaat?csf=1&web=1&e=ytAiCM)
- Examples are provided to quickly show what a composite image looks like and the urban area for a specific town and year


## Limitations & Research suggestions
- The compositing of images has difficulties in some dates when cloud cover is very high leaving out blank areas. 
- The classficiation model selects waves,shiny beaches and rivers as urban area
- Devising the urban area builds on the previous year assuming those pixels are also present in the next year. This assumption is false since buildings can be removed, but was taken to make sure small inconsistencies in the classification model were overlooked. 
- The project is hard coded in tasks specific to Costa Rica, for example, when defining the boundary box (all coastal towns fit in a 5km boundary), and when calculating the growth of developed area (EPSG:8912). 


## References
- ICT - https://www.ict.go.cr/es/noticias-destacadas/2397-costa-rica-recibio-2-6-millones-de-turistas-durante-el-2024.html
- Francini, S., Hermosilla, T., Coops, N. C., Wulder, M. A., White, J. C., & Chirici, G. (2023). An assessment approach for pixel-based image composites. ISPRS Journal of Photogrammetry and Remote Sensing, 202, 1–12. https://doi.org/10.1016/j.isprsjprs.2023.06.002
- SCIJ - https://bienescomunes.fcs.ucr.ac.cr/megaproyecto-en-playa-panama-sintoma-de-una-democracia-ambiental-en-retroceso/ 
- Semanario Universidad - https://semanariouniversidad.com/pais/fiscalia-ambiental-investiga-desde-mayo-supuesto-cambio-de-uso-de-suelo-en-terreno-de-megaproyecto-bahia-papagayo/