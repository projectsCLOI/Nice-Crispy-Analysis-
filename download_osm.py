import osmnx as ox
import geopandas as gpd
place_name = "Tyrol, Austria"
# Set up Overpass query for protected/nature areas in Austria
tags = {
    "boundary": ["protected_area", "national_park"],
    "leisure": "nature_reserve",
}

print("📡 Downloading protected areas from OpenStreetMap (via Overpass)...")
gdf = ox.features_from_place(place_name, tags)

print(f"✅ Retrieved {len(gdf)} features.")

# Keep only polygon geometries
gdf = gdf[gdf.geometry.type.isin(["Polygon", "MultiPolygon"])].copy()

# Reproject to WGS84 (Overpass returns EPSG:4326 by default)
gdf = gdf.set_crs(4326)

# Optionally select relevant columns
cols = [c for c in ["name", "protect_class", "protect_title", "leisure", "boundary", "geometry"] if c in gdf.columns]
gdf = gdf[cols]

# Save to GeoPackage and GeoJSON
gdf.to_file("austria_osm_protected_areas.gpkg", driver="GPKG")
gdf.to_file("austria_osm_protected_areas.geojson", driver="GeoJSON")

print("🎉 Done!")
print(f"Number of protected polygons: {len(gdf)}")
print("📁 Files saved: austria_osm_protected_areas.gpkg, austria_osm_protected_areas.geojson")