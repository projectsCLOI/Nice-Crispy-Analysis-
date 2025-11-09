import geopandas as gpd
import pandas as pd
# Load the data
points = gpd.read_file("Data/200_tyrol_mountains_with_verfied_wiki_data.gpkg")
areas = gpd.read_file("Data/austria_osm_protected_areas.gpkg")

# Ensure both are in the same CRS
if points.crs != areas.crs:
    areas = areas.to_crs(points.crs)

# Perform spatial join
# Suppose the area layer has an attribute 'protection_status'
points_joined = gpd.sjoin(points, areas[['protect_class', 'geometry']], how='left', predicate='within')

# Fill NaN values with "not protected"
points_joined['protect_class'] = points_joined['protect_class'].fillna(0)
points_joined["protect_class"] = pd.to_numeric(points_joined["protect_class"], errors="coerce")
# Keep only the row with the highest 'score' per 'name'
points_joined = points_joined.sort_values("protect_class", ascending=False).drop_duplicates(subset=["name"], keep="first")

# Save result back to a geopackage
points_joined.to_file("Data/200_tyrol_mountains_wiki_protected.gpkg", layer="peaks", driver="GPKG")
