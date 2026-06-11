# Feedback by TAs 
Good proposal, clear plan and doable in the time available. Create the model on asmall subset before applying on multiple mines. Calculate ndvi on small area before upscaleing to entire area before the entire mine arae. Have a look at OpenEO and Eearth engine. Ask staff for help, there is some material available. STAC also will be very usefull. Think about the visualization aa bit more elaboraetly



# Geoscripting project proposal
- Title: A 10 year view of urban development in popular tourist hotspots in Costa Rica 
- Team (or if you already know a team to work with: both team names plus the name of the new team of 4): Broodje kaas en tomaat 
- Numer of the topic chosen (or "own"): own

## Objective and research questions
Define the aim or question(s) of your project, phrased as questions to answer
- How has land use changed in Puerto Viejo, Tamarindo, Santa Teresa, and Uvita
- How much development has ocurred in Puerto Viejo, Tamarindo, Santa Teresa, and Uvita
- Which town has observed most development?
- Enforcing protected area borders: Have development projects violated protected areas?

## Data
Provide a link to the data and describe the metadata (author, date, extent, resolution, etc.)
- We plan to use Sentinel data for our project (possibly Sentinel-1) as there is established precedent of it being used for similar projects
- https://browser.dataspace.copernicus.eu/
- Protected areas vector file: https://www.arcgis.com/home/item.html?id=144883ce0ffc4e8199110972976a137f

Can it be accessed via a script, and how (i.e. API or download link)?
- Sentinel data can be accessed via sits_cube script

Estimate how large the data set will be for your project
- Training data (100 images: 10 per year for 10 years)
- Buffer around Puerto Viejo, Tamarindo, Santa Teresa, and Uvita
- Needs to be refined further, but we were comfortably able to download a tiff covering land area between Jaco & Manuel Antonio National Park, as well as between Limon and Cahuita National Park 
e.g. do this by a little test download of one file unless you decide to work in Google Earth Engine

Important here is to keep the data set small! e.g. below 500 MiB


## Methods
Task 3: Methods (How?)
Which functionality or approach will you use to achieve this? Can you already name new packages you will want to try out?
- Potential Python Packages:  scikit-learn for Kmeans & Random forest, scipy, skimage, PIL

What will be the result, output, and/or visualization?
- Timelapse of urban sprawl (Various yearly images of said tourist hotspots)
- Statistics comparing towns
- Highlighting protected area infrigement if any. 

## Quick workflow overview
- Import data
- Train classification model
- Validate & assess
- Apply to case studies
- Compute temporal change per classified land 
- Compare tourist hotspots
- Overlay protected area on 2025 data
- Plot

#Sources
- https://www.youtube.com/watch?v=2JU3XMkWdPo
- https://www.esa.int/Applications/Observing_the_Earth/Copernicus/Sentinel-1/10_ways_Sentinel-1_data_lets_us_see_our_world
- https://www.youtube.com/watch?v=V6z9PQxFVDY
- https://www.youtube.com/watch?v=rImnDX-FD10 