from pathlib import Path
from typing import Iterable, Dict, Tuple
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from Python.BBox import Bbox

"""" 
Plotting revelant statistics for urban development for given towns referenced in main.py
    Outputs
        For each town it creates:
            - CSV table: urban area for each year
            - CSV table: year with most change 
            - CSV table: percentage change from the start year to the end year of the projects scope
            - PNG line graph: yearly percentage change of developed area
        Town comparisons:
            - CSV table and PNG bar graph: Greatest single year change in developed area for each town
            - CSV table and PNG bar graph: Greatest overall change in developed area for each town
    
    Outline:
        - Core I/O and geometry helpers
        - Time series and change metrics
        - Cross-town comparisons
        - Plotting and saving files
        - Run functions iterating through each town and year (Implemented in main.py) (Recommended to read first)

"""   



###
# Core I/O and geometry helpers
###

def shapefile_path_for(town: str, year: int):
    """
    Return the expected shapefile path for a town/year.
    Args: 
        town: string
        year: integer

    Returns: Path
    """
    return f"Data/{town}/Processed/{town}_{year}.shp".replace(" ", "_")


def load_town_year(town: str, year: int):
    """
    Load a town/year shapefile if present, else return None.
    Args:
        town: string
        year: integer 
    
    Assumes input is in WGS84 (EPSG:4326). The shapefile contains only developed
    polygons; function computes total developed area.

    Returns: DataFrame or None
    """
    shp_path = shapefile_path_for(town, year)
    if not os.path.exists(shp_path):
        print("Could not find town data")
        return None
    try:
        gdf = gpd.read_file(shp_path)
        # Normalize CRS to EPSG:4326 if missing
        if gdf.crs is None:
            gdf.set_crs(epsg=4326, inplace=True)
        elif gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)
        return gdf
    except Exception:
        return None


def developed_area_m2(gdf: gpd.GeoDataFrame):
    """
    Compute total developed area in m² by reprojecting to the Costa Rican EPSG 8912.
    Note: EPSG is hard-coded!
    
    Args:
        gdf: GeoDataFrame of the developed area

    Returns: float value
    """
    epsg = 8912
    gdf_m = gdf.to_crs(epsg=epsg)
    return float(gdf_m.geometry.area.sum())


###
# Time series and change metrics
###

def series_for_town(town: str, years: Iterable[int]):
    """
    Calculates developed area for a given town for given years
    Args:
        - town: string
        - years: interable list of integers

    Returns: pandas Series indexed by year with total developed area (m²)
    """
    data = {}
    for y in years:
        gdf = load_town_year(town, y)
        if gdf is None:
            continue  # skip missing/failed
        data[y] = developed_area_m2(gdf)
    if not data:
        return pd.Series(dtype=float)
    s = pd.Series(data).sort_index()
    return s


def yoy_change(series: pd.Series, decimals: int = 2):
    """
    Year-over-year % change.
    Args:
        - series: pandas Series containing developed area per year
        - decimals: set to 2 decimal places
    
    %Δ = (v_t - v_{t-1}) / v_{t-1} * 100
    If previous value == 0, sets NaN (undefined) to avoid infinities.
    
    Returns: pandas Series float of YoY % change 
    """
    prev = series.shift(1)
    pct = (series - prev) / prev * 100.0
    pct = pct.where(prev != 0)
    return pct.round(decimals)


def start_to_end_change(series: pd.Series, decimals: int = 2):
    """
    % change from first available year to last available year for a town.
    Args: 
        series: pandas Series containing developed area per year
        decimals: set to 2 decimal places

    Returns: float or NAN if a year is missing
    """
    if series.empty:
        return np.nan
    start = series.iloc[0]
    end = series.iloc[-1]
    if start == 0:
        return np.nan
    return round(((end - start) / start) * 100.0, decimals)


def highest_single_year_change(series: pd.Series):
    """
    Calculates (year, %Δ) of the largest absolute YoY change (can be negative).
    Args:
        series: pandas Series containing developed area per year
    
    Year reported corresponds to the current year in the Δ (i.e., t for Δ_t vs t-1).

    Returns: tuple of year and highest %Δ
    """
    pct = yoy_change(series)
    if pct.dropna().empty:
        return (None, None)
    # Use absolute value to find magnitude; keep original sign for reporting.
    idx = pct.abs().idxmax()
    return (int(idx), float(pct.loc[idx]))


###
# Cross-town comparisons
###

def compare_start_to_end_across_towns(series_map: Dict[str, pd.Series], decimals: int = 2):
    """
    Creates table that presents the percentage change in size for each town. 
    Args:
        series: Dictionary with town names as key and value as a pandas Series containing developed area per year
        decimals: set to 2 decimal places

    Returns: DataFrame of total change in developed area for each town
    """
    rows = []
    for town, s in series_map.items():
        rows.append({"town": town, "pct_change_start_to_end": start_to_end_change(s, decimals=decimals)})
    df = pd.DataFrame(rows).set_index("town").sort_values("pct_change_start_to_end", ascending=False)
    return df


def compare_max_single_year_change(series_map: Dict[str, pd.Series]):
    """
    Returns a dataframe (table) that shows the maximum percentage change per town 
    Args:  
        series: Dictionary with town names as key and value as a pandas Series containing developed area per year

    Returns: DataFrame of the highest single year percentage change per town
    """
    rows = []
    for town, s in series_map.items():
        year, pct = highest_single_year_change(s)
        rows.append({"town": town, "year_of_max_change": year, "pct_change": pct})
    df = pd.DataFrame(rows).set_index("town")
    # Sort by absolute magnitude of change, descending
    df = df.assign(_abs=lambda d: d["pct_change"].abs()).sort_values("_abs", ascending=False).drop(columns=["_abs"])
    return df


###
# Plotting and saving files
###

def ensure_dir(p: Path):
    """
    Makes sure directories are created, if it exists it continues.
    Args:
        p: Path 
    """
    p.mkdir(parents=True, exist_ok=True)


def save_yoy_graph(town: str, series: pd.Series, out_root = Path("Output")):
    """ 
    Creates a year over year percentage change for a given town
    Args:
        town: string
        series: pandas Series containing developed area per year
        out_root: Output directory name
    
    Exports: graph
    Returns: Path to the location of the graph
    """
    yoy = yoy_change(series)
    out_dir = out_root / town
    ensure_dir(out_dir)
    out_png = out_dir / f"{town}_yoy_change.png"

    plt.figure()
    yoy.plot(kind="line")
    plt.title(f"Year-over-Year % Change – {town}")
    plt.xlabel("Year")
    plt.ylabel("% Change")
    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    plt.close()
    return out_png


def save_series_table(town: str, series: pd.Series, out_root = Path("Output")):
    """
    Saves a CSV table containing developed area per year
    Args:
        town: string
        series: pandas Series containing developed area per year
        out_root: Root of outputs as "Output"

    Exports: CSV 
    Returns: Path to CSV containing developed area per year
    """
    out_dir = out_root / town
    ensure_dir(out_dir)
    out_csv = out_dir / f"{town}_developed_area_m2.csv"
    series.to_frame(name="developed_area_m2").to_csv(out_csv, index_label="year")
    return out_csv


def save_start_end_table(town: str, series: pd.Series, out_root = Path("Output")):
    """
    Saves a CSV table containing percentage change of developed area during all the years for a given town
    Args:
        town: string
        series: pandas Series containing developed area per year
        out_root: Root of outputs as "Output"

    Exports: CSV 
    Returns: Path to CSV containing total percentage change of developed area for a given town 
    """    
    out_dir = out_root / town
    ensure_dir(out_dir)
    out_csv = out_dir / f"{town}_start_to_end_pct_change.csv"
    val = start_to_end_change(series)
    pd.DataFrame({"town": [town], "pct_change_start_to_end": [val]}).to_csv(out_csv, index=False)
    return out_csv


def save_max_single_year_table(town: str, series: pd.Series, out_root = Path("Output")):
    """
    Saves a CSV table containing percentage change of developed area during all the years for a given town
    Args:
        town: string
        series: pandas Series containing developed area per year
        out_root: Root of outputs as "Output"

    Exports: CSV 
    Returns: Path to CSV containing total percentage change of developed area for a given town 
    """  
    out_dir = out_root / town
    ensure_dir(out_dir)
    out_csv = out_dir / f"{town}_max_single_year_change.csv"
    year, pct = highest_single_year_change(series)
    pd.DataFrame({"town": [town], "year": [year], "pct_change": [pct]}).to_csv(out_csv, index=False)
    return out_csv


def save_comparison_tables(series_map: Dict[str, pd.Series], out_root = Path("Output")):
    """
    Saves 2 CSV tables of town comparisons
    Args:
        town: string
        series: Dictionary with town names as key and value as a pandas Series containing developed area per year
        out_root: Root of outputs as "Output"

    Exports: 2 CSVs
    Returns: Tuple of Paths to CSVs containing the highest total change of developed area for each town, 
             and the highest single year change in area for each town
    """      
    cmp_dir = out_root / "Town_comparisons"
    ensure_dir(cmp_dir)

    df_start_end = compare_start_to_end_across_towns(series_map)
    out1 = cmp_dir / "towns_start_to_end_pct_change.csv"
    df_start_end.to_csv(out1)

    df_max = compare_max_single_year_change(series_map)
    out2 = cmp_dir / "towns_max_single_year_change.csv"
    df_max.to_csv(out2)

    return out1, out2


def save_comparison_graphs(series_map: Dict[str, pd.Series], out_root: Path = Path("Output")):
    """
    Saves 2 PNG graphs  
    Args:
        town: string
        series: Dictionary with town names as key and value as a pandas Series containing developed area per year
        out_root: Root of outputs as "Output"

    Exports: 2 PNGs
    Returns: Tuple of Paths to PNGs containing the highest total change of developed area for each town, 
             and the highest single year change in area for each town
    """     
    cmp_dir = out_root / "Town_comparisons"
    ensure_dir(cmp_dir)

    # Bar of start→end % change per town
    df_start_end = compare_start_to_end_across_towns(series_map)
    out_png1 = cmp_dir / "towns_start_to_end_pct_change.png"
    plt.figure()
    df_start_end["pct_change_start_to_end"].plot(kind="bar")
    plt.title("Start→End % Change by Town")
    plt.xlabel("Town")
    plt.ylabel("% Change")
    plt.tight_layout()
    plt.savefig(out_png1, dpi=200)
    plt.close()

    # Bar of max single-year change magnitude per town (signed values)
    df_max = compare_max_single_year_change(series_map)
    out_png2 = cmp_dir / "towns_max_single_year_change.png"
    plt.figure()
    df_max["pct_change"].plot(kind="bar")
    plt.title("Max Single-Year % Change by Town")
    plt.xlabel("Town")
    plt.ylabel("% Change")
    plt.tight_layout()
    plt.savefig(out_png2, dpi=200)
    plt.close()

    return out_png1, out_png2

def yoy_graph_alltowns(series_map: Dict[str, pd.Series], out_root: Path = Path("Output")):
    """
    """
    cmp_dir = out_root / "Town_comparisons"
    ensure_dir(cmp_dir)

    # Build a wide DataFrame with years as index and towns as columns
    all_years = sorted({y for s in series_map.values() for y in s.index})

    df_ha = pd.DataFrame(index=all_years)
    for town, s in series_map.items():
        df_ha[town] = s.reindex(all_years).astype(float) * 0.0001

    out_png = cmp_dir / "towns_area_growth_ha.png"

    plt.figure()
    for town in df_ha.columns:
        y = df_ha[town]
        if y.dropna().empty:
            continue
        plt.plot(df_ha.index, y.values, marker="o", label=town)

        plt.xlabel("Year")
        plt.ylabel("Developed area (ha)")
        plt.title("Developed Area Growth (ha) – All Towns")
        plt.legend(title="Town", loc="best")
        plt.grid(True, linestyle=":", linewidth=0.5)

    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    plt.close()
    return out_png

def yearly_change_alltowns(series_map: Dict[str, pd.Series], out_root: Path = Path("Output")):
    """
    
    """
    cmp_dir = out_root / "Town_comparisons"
    ensure_dir(cmp_dir)

    # Build a wide DataFrame with years as index and towns as columns
    all_years = sorted({y for s in series_map.values() for y in s.index})
    df = pd.DataFrame(index=all_years)
    for town, s in series_map.items():
        df[town] = series_for_town(town, s) 

    out_png = cmp_dir / "towns_area_change.png"
    plt.figure()
    any_plotted = False
    for town in df.columns:
        y = df[town]
        if y.dropna().empty:
            continue
        # Plot with markers so sparse data is still readable
        plt.plot(df.index, y.values, marker="o", label=town)
        any_plotted = True


        plt.xlabel("Year")
        plt.ylabel("Area (ha)")
        plt.title("Area Change for All Towns")
        plt.legend(title="Town", loc="best")
        plt.grid(True, linestyle=":", linewidth=0.5)

    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    plt.close()
    return out_png

###
# Run functions iterating through each town and year (Implemented in main.py)
###

def build_series_map(town_names, years):
    """
    Creates a dictionary for each town with year and developed area info 
    Args:
        town_names: iterable string
        years: interable integers
    
    Returns: Dictionary
    """
    series_map = {}
    for town in town_names:
        s = series_for_town(town, years)
        if s.empty:
            print(f"[WARN] No data found for {town}; skipping.")
            continue
        series_map[town] = s
    return series_map


def save_per_town_artifacts(series_map):
    """
    Runs functions to compute and save tables and graphs for each town
    Args:
        series_map: Dictionary with town names as key and value as a pandas Series containing developed area per year
    
    Returns: for each town a table of developed area per year, 
            a line graph of the percentage change per year, 
            a table of the total % change in developed area
            a table of the highest % change in developed area 
    """

    for town, s in series_map.items():
        # CSV with absolute developed area by year
        p1 = save_series_table(town, s)
        # YoY % change graph
        p2 = save_yoy_graph(town, s)
        # Start→End % change table
        p3 = save_start_end_table(town, s)
        # Max single-year % change table
        p4 = save_max_single_year_table(town, s)
        print(f"Saved: {p1}\n       {p2}\n       {p3}\n       {p4}")


def save_cross_town_artifacts(series_map: Dict[str, pd.Series]):
    """
    Runs functions to compute and save tables and graphs comparing towns
    Args:
        series_map: Dictionary with town names as key and value as a pandas Series containing developed area per year
    
    Returns: Tables and graphs for highest total change of developed area for each town, 
             and the highest single year change in area for each town
    """
    t1, t2 = save_comparison_tables(series_map)
    g1, g2 = save_comparison_graphs(series_map)
    g3 = yoy_graph_alltowns(series_map)
    g4 = yearly_change_alltowns(series_map)
    print(f"Saved comparisons: {t1}, {t2}, {g1}, {g2}, {g3}, {g4}")



def save_stats(towns, years):
    town_names = list(towns.keys())
    series_map = build_series_map(town_names, years)
    if not series_map:
        print("[ERROR] No town/year series built. Check your Data/ directory structure and filenames.")
    save_per_town_artifacts(series_map)
    save_cross_town_artifacts(series_map)



