import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# Load your layers (assuming they are in the same GeoPackage)
perfect_gpkg = "points_with_avg.gpkg"

# Read layers
gdf_lines = gpd.read_file(perfect_gpkg, layer="strava_segments")
gdf_points = gpd.read_file(perfect_gpkg, layer="peaks")


# Path to your CSV
csv_path = "./Data/ppl_on_mountains_tyrol_cleaned.csv"

# Read the CSV
df = pd.read_csv(csv_path)

# Make sure your columns are named correctly
# (adjust if your CSV uses different names)
lat_col = "lat"
lon_col = "lon"

# Create Point geometries
geometry = [Point(xy) for xy in zip(df[lon_col], df[lat_col])]

# Create GeoDataFrame
webcam_points = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

# Make sure both are in the same CRS
if gdf_points.crs != webcam_points.crs:
    webcam_points = webcam_points.to_crs(gdf_points.crs)

# --- Make sure both use the same CRS ---
if webcam_points.crs != gdf_points.crs:
    webcam_points = webcam_points.to_crs(gdf_points.crs)

# --- Reproject to a metric CRS if currently in degrees ---
# (e.g., UTM or Web Mercator for distance in meters)
if gdf_points.crs.is_geographic:
    gdf_points   = gdf_points.to_crs(3857)
    webcam_points = webcam_points.to_crs(3857)

# --- Create buffers (e.g., 1000 m radius) ---
buffer_distance = 5000  # meters
gdf_points["geometry_buffer"] = gdf_points.geometry.buffer(buffer_distance)

# Create a GeoDataFrame with buffers
gdf_points = gdf_points.set_geometry("geometry_buffer")

# --- Spatial join: which points fall within which buffer ---
join = gpd.sjoin(webcam_points, gdf_points, predicate="within", how="inner")

# --- Sum point values within each buffer ---
sum_values = join.groupby("index_right")["count"].sum()

# --- Add sums back to reference points ---
gdf_points["people_on_webcams"] = gdf_points.index.map(sum_values).fillna(0)

# Write to GeoPackage
webcam_points.to_file("peaks_strava_wiki_web.gpkg", layer="webcams", driver="GPKG")
gdf_lines.to_file("peaks_strava_wiki_web.gpkg", layer="strava_segments", driver="GPKG")
gdf_points = gdf_points.drop(columns=["geometry_buffer"])
gdf_points.to_file("peaks_strava_wiki_web.gpkg", layer="peaks", driver="GPKG")