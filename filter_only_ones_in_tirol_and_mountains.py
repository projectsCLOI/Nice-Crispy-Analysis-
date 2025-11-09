import geopandas as gpd

# --- Load your Wikidata-enriched GeoPackage ---
gdf = gpd.read_file("tyrol_peaks_top200_wikidata.gpkg")

# --- Filter only mountains located in Tyrol ---
gdf_filtered = gdf[(gdf["is_mountain"] == True) & (gdf["in_tyrol"] == True)].copy()

print(f"✅ Found {len(gdf_filtered)} peaks that are mountains in Tyrol.")

# --- Save to new GeoPackage ---
output_file = "top_tyrol_mountains.gpkg"
gdf_filtered.to_file(output_file, driver="GPKG")

print(f"📁 Saved filtered dataset to: {output_file}")