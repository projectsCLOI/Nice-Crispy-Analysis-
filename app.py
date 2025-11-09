import streamlit as st
import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from styles import STYLE_CSS

st.set_page_config(
    page_title="Tyrol Outdoor Usage", layout="wide", initial_sidebar_state="collapsed"
)

st.markdown(STYLE_CSS, unsafe_allow_html=True)

# ----------------------------LOAD DATA----------------------------------------


@st.cache_data
def load_data():
    # load stress score data
    peaks = gpd.read_file("Data/200_tyrol_mountains_final_stress_score.gpkg", layer="peaks")
    protected = gpd.read_file("Data/austria_osm_protected_areas.gpkg")

    if peaks.crs != protected.crs:
        protected = protected.to_crs(peaks.crs)

    peaks = peaks.to_crs("EPSG:4326")
    protected = protected.to_crs("EPSG:4326")

    peaks["latitude"] = peaks.geometry.y
    peaks["longitude"] = peaks.geometry.x

    # change ele values to numerics
    if "ele" in peaks.columns:
        peaks["ele"] = pd.to_numeric(peaks["ele"], errors="coerce")

    stress_col = None
    for col in ["stress_score", "final_stress_score", "stress", "score"]:
        if col in peaks.columns:
            peaks[col] = pd.to_numeric(peaks[col], errors="coerce")
            stress_col = col
            break
    print(stress_col)
    return peaks, protected, stress_col


peaks, protected, stress_col = load_data()

# ---------------------------------HEADER---------------------------------------
st.title("Tyrol Outdoor Usage Dashboard")
st.markdown("Insights into outdoor usage and environmental stress in the Tyrol region")
st.markdown("---")

# ---------------------------------METRICS--------------------------------------
col1, col2, col3, col4 = st.columns(4)

# total peaks with data
with col1:
    st.metric(label="Total Peaks", value=f"{len(peaks):,}")

# total stressed areas
with col2:
    if stress_col:
        healthy_areas = len(peaks[peaks[stress_col] > 0])
        st.metric(label="Stressed Areas", value=f"{healthy_areas:,}")
    else:
        st.metric(label="Stressed Areas", value="N/A")

# average stress score in the region
with col3:
    if stress_col:
        avg_stress = peaks[stress_col].mean()
        st.metric(label="Avg Stress Score", value=f"{avg_stress:.2f}")
    else:
        st.metric(label="Avg Stress Score", value="N/A")

# amount of protected areas
with col4:
    st.metric(label="Protected Areas", value=f"{len(protected):,}")

st.markdown("---")

# ------------------------FILTERS UNDER METRICS (COLLAPSIBLE)-------------------
with st.expander("Filters", expanded=False):
    col_filter1, col_filter2 = st.columns([1, 2])

    with col_filter1:
        st.subheader("Search & Filters")

        # search bar
        search_input = st.text_input("Search Peak Name")

        # checkbox - if checked then the protected area locations will be displayed
        show_protected = st.checkbox("Show Protected Areas", value=False)

        # slider for elevation
        if "ele" in peaks.columns:
            valid = peaks["ele"].dropna()
            if len(valid) > 0:
                min_ele, max_ele = float(valid.min()), float(valid.max())
                elevation_range = st.slider(
                    "Elevation Range (m)",
                    min_value=min_ele,
                    max_value=max_ele,
                    value=(min_ele, max_ele),
                )
            else:
                elevation_range = None
        else:
            elevation_range = None

        # stress score slider
        if stress_col:
            valid_stress = peaks[stress_col].dropna()
            if len(valid_stress) > 0:
                min_stress, max_stress = (
                    float(valid_stress.min()),
                    float(valid_stress.max()),
                )
                stress_range = st.slider(
                    "Stress Score Range",
                    min_value=min_stress,
                    max_value=max_stress,
                    value=(min_stress, max_stress),
                )
            else:
                stress_range = None
        else:
            stress_range = None

    with col_filter2:
        pass

# ------------------------DATA FILTERING---------------------------------------
filtered_peaks = peaks.copy()

# filter by search input
if search_input and "name" in filtered_peaks.columns:
    matches = filtered_peaks[
        filtered_peaks["name"].str.contains(search_input, case=False, na=False)
    ]
    if len(matches) > 0:
        filtered_peaks = matches
    else:
        st.warning("Area not found")
        filtered_peaks = peaks.copy()

# filter by elevation
if elevation_range and "ele" in filtered_peaks.columns:
    filtered_peaks = filtered_peaks[
        (filtered_peaks["ele"] >= elevation_range[0])
        & (filtered_peaks["ele"] <= elevation_range[1])
    ]

# filter by stress score
if stress_range and stress_col:
    filtered_peaks = filtered_peaks[
        (filtered_peaks[stress_col] >= stress_range[0])
        & (filtered_peaks[stress_col] <= stress_range[1])
    ]

# ------------------------MAP AND CHARTS--------------------------------------
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Interactive Map")

    if show_protected:
        prot = protected.copy()

        prot["lat"] = prot.geometry.centroid.y
        prot["lon"] = prot.geometry.centroid.x

        fig_map = px.scatter_mapbox(
            prot,
            lat="lat",
            lon="lon",
            hover_name="name" if "name" in prot.columns else None,
            hover_data=None,
            color_discrete_sequence=["green"],
            zoom=8,
            height=500,
        )

        fig_map.update_traces(marker=dict(size=12))

    else:
        hover_data_dict = {}
        if "ele" in filtered_peaks.columns:
            hover_data_dict["ele"] = ":.0f"
        if stress_col:
            hover_data_dict[stress_col] = ":.2f"

        fig_map = px.scatter_mapbox(
            filtered_peaks,
            lat="latitude",
            lon="longitude",
            hover_name="name" if "name" in filtered_peaks.columns else None,
            hover_data=hover_data_dict if hover_data_dict else None,
            color=stress_col
            if stress_col
            else ("ele" if "ele" in filtered_peaks.columns else None),
            color_continuous_scale="RdYlGn_r" if stress_col else "Viridis",
            zoom=8,
            height=500,
            labels={stress_col: "Stress Score"} if stress_col else None,
        )

        fig_map.update_traces(marker=dict(size=12))

    fig_map.update_layout(
        mapbox_style="open-street-map", margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )

    st.plotly_chart(fig_map, use_container_width=True)

with col2:
    st.subheader("Statistics")

    if show_protected:
        st.info("Statistics off for protected areas.")

    else:
        if stress_col:
            # histogram
            fig_hist = px.histogram(
                filtered_peaks,
                x=stress_col,
                nbins=30,
                labels={stress_col: "Stress Score", "count": "Number of Peaks"},
                title="Stress Score Distribution",
            )
            fig_hist.update_layout(
                height=250, margin=dict(l=0, r=0, t=30, b=0), showlegend=False
            )
            st.plotly_chart(fig_hist, use_container_width=True)

            # highest stress scores
            st.markdown("**Top 10 Highest Stress Scores**")
            if "name" in filtered_peaks.columns:
                top_stress = filtered_peaks.nlargest(10, stress_col)[
                    ["name", stress_col]
                ]
                top_stress.columns = ["Peak Name", "Stress Score"]
                st.dataframe(
                    top_stress.reset_index(drop=True),
                    use_container_width=True,
                    hide_index=True,
                    height=250,
                )
            else:
                st.info("Peak names not available.")
        else:
            st.warning("Stress score data not found in the dataset.")


# ------------------------STRESS SCORE RANGE ANALYSIS-----------------------------
if stress_col:
    st.subheader("Peaks by Stress Score Range")

    bins = [-1, -0.6, -0.2, 0.2, 0.6, 1.0]
    labels = [
        "Very Low (-1 to -0.6)",
        "Low (-0.6 to -0.2)",
        "Moderate (-0.2 to 0.2)",
        "High (0.2 to 0.6)",
        "Very High (0.6 to 1.0)",
    ]

    filtered_peaks["stress_range"] = pd.cut(
        filtered_peaks[stress_col], bins=bins, labels=labels, include_lowest=True
    )

    range_counts = filtered_peaks["stress_range"].value_counts().sort_index()

    col1, col2 = st.columns(2)

    # bar chart
    with col1:
        color_map = {
            "Very Low (-1 to -0.6)": "#d7191c",
            "Low (-0.6 to -0.2)": "#fdae61",
            "Moderate (-0.2 to 0.2)": "#ffffbf",
            "High (0.2 to 0.6)": "#a6d96a",
            "Very High (0.6 to 1.0)": "#1a9641",
        }

        fig_bar = px.bar(
            x=range_counts.index,
            y=range_counts.values,
            labels={"x": "Stress Score Range", "y": "Number of Peaks"},
            title="Peak Distribution by Stress Level",
            color=range_counts.index,
            color_discrete_map=color_map,
        )
        fig_bar.update_layout(
            height=350, margin=dict(l=0, r=0, t=30, b=0), showlegend=False
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # pie chart
    with col2:
        color_map = {
            "Very Low (-1 to -0.6)": "#d7191c",
            "Low (-0.6 to -0.2)": "#fdae61",
            "Moderate (-0.2 to 0.2)": "#ffffbf",
            "High (0.2 to 0.6)": "#a6d96a",
            "Very High (0.6 to 1.0)": "#1a9641",
        }

        range_counts_filtered = range_counts[range_counts > 0]

        fig_pie = px.pie(
            values=range_counts_filtered.values,
            names=range_counts_filtered.index,
            title="Percentage Distribution",
            hole=0.4,
            color=range_counts_filtered.index,
            color_discrete_map=color_map,
        )
        fig_pie.update_layout(height=350, margin=dict(l=0, r=0, t=30, b=0))

        st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")

# ------------------------DATA TABLE------------------------------------------
st.subheader("Peak Stress Details")

display_cols = []
if "name" in filtered_peaks.columns:
    display_cols.append("name")
if stress_col:
    display_cols.append(stress_col)
if "ele" in filtered_peaks.columns:
    display_cols.append("ele")
display_cols.extend(["latitude", "longitude"])

display_df = filtered_peaks[display_cols].copy()

# stress score table sorted by stress
if stress_col:
    display_df = display_df.sort_values(by=stress_col, ascending=False)


if "ele" in display_df.columns:
    display_df["ele"] = display_df["ele"].round(0)
if stress_col:
    display_df[stress_col] = display_df[stress_col].round(3)

column_rename = {
    "name": "Peak Name",
    "ele": "Elevation (m)",
    "latitude": "Latitude",
    "longitude": "Longitude",
}
if stress_col:
    column_rename[stress_col] = "Stress Score"

display_df = display_df.rename(columns=column_rename)

st.dataframe(display_df, use_container_width=True, hide_index=True, height=400)

# ------------------------FOOTER----------------------------------------------
st.markdown("---")

st.markdown("*Data source: OpenStreetMap & Stress Score Analysis*")
