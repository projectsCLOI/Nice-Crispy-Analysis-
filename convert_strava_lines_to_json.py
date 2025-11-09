import json
import geopandas as gpd
from shapely.geometry import LineString
from polyline import decode  # pip install polyline
import pandas as pd


perfect_gpkg = "Data/200_tyrol_mountains_wiki_protected.gpkg"
# Load your JSON
with open("./Data/segments2.json") as f:
    data = json.load(f)

features = []
for seg in data:
    poly = seg.get("map", {}).get("polyline")
    if not poly:
        continue

    # Decode polyline -> list of (lat, lon)
    coords = decode(poly)
    print(coords)
    # polyline returns (lat, lon) but shap ely wants (lon, lat)
    line = LineString([(lon, lat) for lat, lon in coords])

    features.append({
        "id": seg["id"],
        "name": seg.get("name"),
        "activity_type": seg.get("activity_type"),
        "distance": seg.get("distance"),
        "city": seg.get("city"),
        "state": seg.get("state"),
        "country": seg.get("country"),
        "effort_count": seg.get("effort_count"),
        "athlete_count": seg.get("athlete_count"),
        "star_count": seg.get("star_count"),
        "start_latlng": seg.get("start_latlng"),
        "end_latlng": seg.get("end_latlng"),
        "created_at": seg.get("created_at"),
        "updated_at": seg.get("updated_at"),
        "geometry": line
    })

# Convert to GeoDataFrame
gdf = gpd.GeoDataFrame(features, crs="EPSG:4326")
# Parse the dates
gdf['created_at'] = pd.to_datetime(gdf['created_at'])

if gdf["created_at"].dt.tz is None:
    # created_at is tz-naive
    now = pd.Timestamp.now(tz=None)
else:
    # created_at is tz-aware
    now = pd.Timestamp.now(tz=gdf["created_at"].dt.tz)
# Calculate timespan in years
gdf['timespan_years'] = (now - gdf['created_at']).dt.total_seconds() / (365.25 * 24 * 3600)

# Avoid division by zero (if created_at == updated_at)
gdf['timespan_years'] = gdf['timespan_years'].replace(0, 1/365.25)  # assume 1 day if zero

# Calculate athlete_count_per_year
gdf['athlete_count_per_year'] = gdf['athlete_count'] / gdf['timespan_years']

# Optional: round to 2 decimals
gdf['athlete_count_per_year'] = gdf['athlete_count_per_year'].round(2)
# Write to GeoPackage
gdf.to_file(perfect_gpkg, layer="strava_segments", driver="GPKG")

print(f"Wrote {len(gdf)} LineStrings to 'segments.gpkg'")