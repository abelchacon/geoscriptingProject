#Cuddly kaas en cunning tomaat
#Geoscripting 2025 Final Project
#Script for plotting raster data

#import necessary packages 
import matplotlib.pyplot as plt
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch
import os
from Python.BBox import Bbox

def year_plot(bbox: Bbox, year, buffer_extent=-0.25): #function works!!!

    """
    Plots the developed areas for a given year with an ESRI World Imagery basemap,
    north arrow, scale bar, and legend. The plot is zoomed into the area of interest.
     
    town: path to the shapefile for the town
    year: year of the shapefile (e.g., 2016)
    bound_extent: buffer around the polygon to zoom in (e.g., -0.25 for 25% zoom in)

    Returns: a plot of the developed areas with basemap and saves it as a PNG file.
    """
    name = bbox.name.replace(" ", "_")
    town = f"Data/{name}/Processed/{name}_{year}.shp"
    #open the vector file
    gdf = gpd.read_file(town)
    # Extract and format town name from file path
    town_name = bbox.name 
    #reproject to Web Mercator for basemap
    gdf_merc = gdf.to_crs(epsg=3857)
    #set plot color
    color = 'red'
    #plot with basemap
    import contextily as ctx
    ax = gdf_merc.plot(figsize=(10, 10), alpha=0.7, color=color, label="Developed area")
    #zoom into polygon
    bounds = gdf_merc.total_bounds  # [minx, miny, maxx, maxy]
    buffer = buffer_extent  # sets buffer around the polygon
    x_range = bounds[2] - bounds[0]
    y_range = bounds[3] - bounds[1]

    # Make it square: expand the shorter side
    max_range = max(x_range, y_range)

    # Compute the center of the current bounds
    x_center = (bounds[0] + bounds[2]) / 2
    y_center = (bounds[1] + bounds[3]) / 2

    # Apply buffer and make limits square
    x_half = (max_range / 2) * (1 + 2 * buffer)
    y_half = (max_range / 2) * (1 + 2 * buffer)

    ax.set_xlim(x_center - x_half, x_center + x_half)
    ax.set_ylim(y_center - y_half, y_center + y_half)

    #add basemap
    ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery, zoom=15)
    #Remove axis tick labels
    ax.set_xticks([])
    ax.set_yticks([])
    #plot title & legend
    ax.set_title(f"Developed Areas in {town_name}, {year}", fontsize=14, fontweight='bold')
    legend_elements = [Patch(facecolor=color, alpha=0.7, label='Developed area')]
    ax.legend(handles=legend_elements, loc='lower right') 
    #add scale bar
    from matplotlib_scalebar.scalebar import ScaleBar
    scalebar = ScaleBar(dx=1, units="m", location='upper right')
    ax.add_artist(scalebar) #works but needs adjustment
    #add north arrow
    ax.annotate('N', xy=(0.1, 0.9), xytext=(0.1, 0.8),
                arrowprops=dict(facecolor='white', width=5, headwidth=15),
                ha='center', va='center', fontsize=20, color="white",
                xycoords=ax.transAxes) #works but needs adjustment

    #save the plot to an output folder
    output_filename = f"{town_name}_{year}_map.png"
    output_path = os.path.join("Output", output_filename)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Map saved to {output_path}")
    #plot the vector file
    # plt.show()
    return gdf


def animated_plot(bbox: Bbox, years, buffer_percent=-25):
    """
    Creates an animated plot showing the developed areas over the years.
    
    plot_paths: list of paths to shapefiles for each year
    years: list of years corresponding to the shapefiles
    buffer_percent: percentage to buffer the plot extent (negative to zoom in)
    
    Returns: an animated plot object.
    """
    from matplotlib.animation import FuncAnimation
    import contextily as ctx
    # Read shapefiles and 
    plot_paths = []
    for year in years:
        name = bbox.name.replace(" ", "_")
        plot_paths.append(f"Data/{name}/Processed/{name}_{year}.shp")
    gdfs = [gpd.read_file(path).to_crs(epsg=3857) for path in plot_paths]
    # Get total bounds from all years
    total_bounds = gpd.GeoDataFrame(pd.concat(gdfs)).total_bounds

    x_range = total_bounds[2] - total_bounds[0]
    y_range = total_bounds[3] - total_bounds[1]

    # --- 🟩 Make it square ---
    max_range = max(x_range, y_range)
    x_center = (total_bounds[0] + total_bounds[2]) / 2
    y_center = (total_bounds[1] + total_bounds[3]) / 2

    # Convert buffer_percent (e.g., -25%) to a scaling factor
    buffer = buffer_percent / 100.0

    # Apply buffer and make limits square
    x_half = (max_range / 2) * (1 + 2 * buffer)
    y_half = (max_range / 2) * (1 + 2 * buffer)

    # Final zoomed/squared bounds
    zoomed_bounds = [
        x_center - x_half,
        y_center - y_half,
        x_center + x_half,
        y_center + y_half
    ]
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 10))

    def update(frame):

        ax.clear()
        from matplotlib_scalebar.scalebar import ScaleBar
        scalebar = ScaleBar(dx=1, units="m", location='upper right')
        ax.add_artist(scalebar) #works but needs adjustment
        #add north arrow
        ax.annotate('N', xy=(0.1, 0.9), xytext=(0.1, 0.8),
                    arrowprops=dict(facecolor='white', width=5, headwidth=15),
                    ha='center', va='center', fontsize=20, color="white",
                    xycoords=ax.transAxes) #works but needs adjustment
        gdfs[frame].plot(ax=ax, color='red', alpha=0.7, label="Developed Land")
        ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery, zoom=15)
        ax.set_title(f"Developed Areas in {name} - {years[frame]}",
                     fontsize=14, fontweight='bold')
        legend_elements = [Patch(facecolor='red', alpha=0.7, label='Developed area')]
        ax.legend(handles=legend_elements, loc='lower right')
        ax.set_xlim(zoomed_bounds[0], zoomed_bounds[2])
        ax.set_ylim(zoomed_bounds[1], zoomed_bounds[3])
        ax.set_xticks([])
        ax.set_yticks([])
    ani = FuncAnimation(fig, update, frames=len(gdfs), repeat=True, interval=1000)
    plt.show()
    return ani
