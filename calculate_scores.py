import geopandas as gpd
import numpy as np
# Load your layers (assuming they are in the same GeoPackage)
perfect_gpkg = "peaks_strava_wiki_web.gpkg"

# Read layers
gdf_lines = gpd.read_file(perfect_gpkg, layer="strava_segments")
gdf_webcams = gpd.read_file(perfect_gpkg, layer="webcams")
gdf_points = gpd.read_file(perfect_gpkg, layer="peaks")

import pandas as pd


def weighted_mean_columns(gdf, columns, weights=None, result_col="weighted_sum"):
    """
    Add several columns together with optional weights.
    Only non-null values are considered in the addition.

    Parameters
    ----------
    gdf : GeoDataFrame
        Input GeoDataFrame.
    columns : list[str]
        List of column names to combine.
    weights : list[float] or None
        Optional weights for each column. If None, all non-null values get equal weight.
    result_col : str
        Name of the resulting column.

    Returns
    -------
    GeoDataFrame
        Copy of the GeoDataFrame with a new column containing the weighted sum.
    """
    df = gdf.copy()

    if weights is not None:
        if len(weights) != len(columns):
            raise ValueError("Length of weights must match length of columns")

    def weighted_row(row):
        vals = [row[c] for c in columns if pd.notnull(row[c])]
        if not vals:
            return np.nan
        if weights is None:
            w = [1 / len(vals)] * len(vals)
        else:
            # normalize weights but only for non-null columns
            valid_weights = [w for c, w in zip(columns, weights) if pd.notnull(row[c])]
            s = sum(valid_weights)
            w = [vw / s for vw in valid_weights]
        return np.dot(vals, w)

    df[result_col] = df.apply(weighted_row, axis=1)
    return df


# higher score is more popularity
gdf_points["wikipedia_views"]= np.log( gdf_points["wikipedia_views"] )
gdf_points["avg_athlete_count_per_year"]= np.log( gdf_points["avg_athlete_count_per_year"] )
gdf_points["wiki_pop_measure"] = gdf_points["wikipedia_views"] / gdf_points["wikipedia_views"].max()
gdf_points["strava_pop_measure"] = gdf_points["avg_athlete_count_per_year"] / gdf_points["avg_athlete_count_per_year"].max()
gdf_points.loc[gdf_points["people_on_webcams"] == 0, "people_on_webcams"] = np.nan
gdf_points["webcam_pop_measure"] = gdf_points["people_on_webcams"] / gdf_points["people_on_webcams"].max()
gdf_points = weighted_mean_columns(gdf_points, ["wiki_pop_measure", "strava_pop_measure", "webcam_pop_measure"],
                                   result_col="gdf_total_popularity_score")

mapping = {0: 0.9, 4: 0.7, 5: 0.6}
gdf_points["protect_threshold"] = gdf_points["protect_class"].map(mapping)

gdf_points["stress_score"] = gdf_points["gdf_total_popularity_score"] - gdf_points["protect_threshold"]

# Save updated points layer to GeoPackage
gdf_webcams.to_file("200_tyrol_mountains_final_stress_score.gpkg", layer="webcams", driver="GPKG")
gdf_points.to_file("200_tyrol_mountains_final_stress_score.gpkg", layer="peaks", driver="GPKG")
gdf_lines.to_file("200_tyrol_mountains_final_stress_score.gpkg", layer="strava_segments", driver="GPKG")