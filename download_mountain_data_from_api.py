import osmnx as ox
import geopandas as gpd

# Query for mountain peaks in Tyrol (or Austria)
place_name = "Tyrol, Austria"
tags = {"natural": "peak"}

print(f"📡 Downloading mountain peaks in {place_name}...")
peaks = ox.features_from_place(place_name, tags=tags)

# Keep only point geometries
peaks = peaks[peaks.geometry.type == "Point"].copy()

# Optional: select relevant fields
cols = [c for c in ["name", "ele", "geometry"] if c in peaks.columns]
peaks = peaks[cols]

# Save locally
peaks.to_file("tyrol_mountain_peaks.gpkg", driver="GPKG")

print(f"✅ Saved {len(peaks)} peaks.")