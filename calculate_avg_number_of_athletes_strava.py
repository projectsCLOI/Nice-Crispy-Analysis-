import geopandas as gpd

# Load your layers (assuming they are in the same GeoPackage)
perfect_gpkg = "Data/200_tyrol_mountains_wiki_protected.gpkg"

# Read layers
gdf_lines = gpd.read_file(perfect_gpkg, layer="strava_segments")
gdf_points = gpd.read_file(perfect_gpkg, layer="peaks")

# Reproject to a local UTM (metric) CRS
# This uses the centroid of the lines to pick an appropriate UTM zone
centroid = gdf_lines.unary_union.centroid
utm_zone = int((centroid.x + 180) // 6) + 1
utm_crs = f"EPSG:{32600 + utm_zone}"  # WGS84 / UTM northern hemisphere
print("Using projected CRS:", utm_crs)

gdf_lines = gdf_lines.to_crs(utm_crs)
gdf_points = gdf_points.to_crs(utm_crs)

# Create buffer in meters
buffer_distance = 5000  # meters
gdf_points['geometry_buffer'] = gdf_points.geometry.buffer(buffer_distance)
gdf_points = gdf_points.drop(columns=["index_right"])
# Spatial join
joined = gpd.sjoin(
    gpd.GeoDataFrame(gdf_lines, geometry=gdf_lines.geometry),
    gpd.GeoDataFrame(gdf_points, geometry='geometry_buffer'),
    how='inner',
    predicate='intersects'
)

# Average athlete_count_per_year per point
avg_per_point = joined.groupby('index_right')['athlete_count_per_year'].mean()

# Add back to points GeoDataFrame
gdf_points['avg_athlete_count_per_year'] = gdf_points.index.map(avg_per_point)

# Drop temporary buffer
gdf_points = gdf_points.drop(columns=['geometry_buffer'])

# Reproject back to WGS84 if needed
gdf_points = gdf_points.to_crs("EPSG:4326")

# Save updated points layer to GeoPackage
gdf_points.to_file("points_with_avg.gpkg", layer="peaks", driver="GPKG")
gdf_lines.to_file("points_with_avg.gpkg", layer="strava_segments", driver="GPKG")