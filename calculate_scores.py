import geopandas as gpd
import numpy as np
# Load your layers (assuming they are in the same GeoPackage)
perfect_gpkg = "points_with_avg.gpkg"

# Read layers
gdf_lines = gpd.read_file(perfect_gpkg, layer="strava_segments")
gdf_points = gpd.read_file(perfect_gpkg, layer="peaks")

# higher score is more popularity
gdf_points["wikipedia_views"]= np.log( gdf_points["wikipedia_views"] )
gdf_points["avg_athlete_count_per_year"]= np.log( gdf_points["avg_athlete_count_per_year"] )
gdf_points["wiki_pop_measure"] = gdf_points["wikipedia_views"] / gdf_points["wikipedia_views"].max()
gdf_points["strava_pop_measure"] = gdf_points["avg_athlete_count_per_year"] / gdf_points["avg_athlete_count_per_year"].max()
wiki_weight = 0.5
strava_weight = 0.5
assert (wiki_weight + strava_weight) == 1.0
gdf_points["gdf_total_popularity_score"] = (gdf_points["wiki_pop_measure"]* wiki_weight + gdf_points["strava_pop_measure"] *strava_weight)
# map protect_class to protect_threshold
mapping = {0: 0.9, 4: 0.7, 5: 0.6}
gdf_points["protect_threshold"] = gdf_points["protect_class"].map(mapping)

gdf_points["stress_score"] = gdf_points["gdf_total_popularity_score"] - gdf_points["protect_threshold"]

# Save updated points layer to GeoPackage
gdf_points.to_file("200_tyrol_mountains_final_stress_score.gpkg", layer="peaks", driver="GPKG")
gdf_lines.to_file("200_tyrol_mountains_final_stress_score.gpkg", layer="strava_segments", driver="GPKG")