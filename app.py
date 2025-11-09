import streamlit as st
import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from styles import STYLE_CSS

st.set_page_config(
    page_title="Tyrol Outdoor Usage",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown(STYLE_CSS, unsafe_allow_html=True)

#----------------------------LOAD DATA----------------------------------------

@st.cache_data
def load_data():
    peaks = gpd.read_file("Data/tyrol_mountain_peaks.gpkg")
    protected = gpd.read_file("Data/austria_osm_protected_areas.gpkg")
    
    if peaks.crs != protected.crs:
        protected = protected.to_crs(peaks.crs)
    
    peaks = peaks.to_crs("EPSG:4326")
    protected = protected.to_crs("EPSG:4326")
    
    peaks['latitude'] = peaks.geometry.y
    peaks['longitude'] = peaks.geometry.x
    
    if 'ele' in peaks.columns:
        peaks['ele'] = pd.to_numeric(peaks['ele'], errors='coerce')
    
    return peaks, protected

peaks, protected = load_data()

#---------------------------------HEADER---------------------------------------
st.title("Tyrol Outdoor Usage Dashboard")
st.markdown("Insights into outdoor usage in the Tyrol region")
st.markdown("---")

#---------------------------------METRICS--------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Total Peaks", value=f"{len(peaks):,}")

with col2:
    if 'ele' in peaks.columns:
        avg_elevation = peaks['ele'].mean()
        st.metric(label="Avg Elevation", value=f"{avg_elevation:,.0f} m")
    else:
        st.metric(label="Avg Elevation", value="N/A")

with col3:
    if 'ele' in peaks.columns:
        max_peak = peaks['ele'].max()
        st.metric(label="Highest Peak", value=f"{max_peak:,.0f} m")
    else:
        st.metric(label="Highest Peak", value="N/A")

with col4:
    st.metric(label="Protected Areas", value=f"{len(protected):,}")

st.markdown("---")

#------------------------FILTERS UNDER METRICS (COLLAPSIBLE)-------------------
with st.expander("Filters", expanded=False):
    col_filter1, col_filter2 = st.columns([1, 2])

    with col_filter1:
        st.subheader("Search & Filters")

        # search bar
        search_input = st.text_input("Search Peak Name")

        # checkboxx
        show_protected = st.checkbox("Show just Protected Areas", value=True) 

        # data slider
        if 'ele' in peaks.columns:
            valid = peaks['ele'].dropna()
            if len(valid) > 0:
                min_ele, max_ele = float(valid.min()), float(valid.max())
                elevation_range = st.slider(
                    "Elevation Range (m)",
                    min_value=min_ele,
                    max_value=max_ele,
                    value=(min_ele, max_ele)
                )
            else:
                elevation_range = None
        else:
            elevation_range = None

    with col_filter2:
        pass  

#------------------------DATA FILTERING---------------------------------------
filtered_peaks = peaks.copy()

# filter by search input
if search_input and 'name' in filtered_peaks.columns:
    matches = filtered_peaks[filtered_peaks['name'].str.contains(search_input, case=False, na=False)]
    if len(matches) > 0:
        filtered_peaks = matches
    else:
        st.warning("Area not found")
        filtered_peaks = peaks.copy() 

# filter by elevation
if elevation_range and 'ele' in filtered_peaks.columns:
    filtered_peaks = filtered_peaks[
        (filtered_peaks['ele'] >= elevation_range[0]) &
        (filtered_peaks['ele'] <= elevation_range[1])
    ]

#------------------------MAP AND CHARTS--------------------------------------
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Interactive Map")

    # If checkbox is checked → show protected areas ONLY
    if show_protected:
        prot = protected.copy()

        # centroid coordinates for display
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
            height=500
        )

    # Checkbox not checked → show peaks ONLY
    else:
        fig_map = px.scatter_mapbox(
            filtered_peaks,
            lat='latitude',
            lon='longitude',
            hover_name='name' if 'name' in filtered_peaks.columns else None,
            hover_data={'ele': ':.0f'} if 'ele' in filtered_peaks.columns else None,
            color='ele' if 'ele' in filtered_peaks.columns else None,
            color_continuous_scale='Viridis' if 'ele' in filtered_peaks.columns else None,
            zoom=8,
            height=500,
        )

    fig_map.update_layout(
        mapbox_style="open-street-map",
        margin={"r":0, "t":0, "l":0, "b":0}
    )

    st.plotly_chart(fig_map, use_container_width=True)

with col2:
    st.subheader("Statistics")

    # No peak stats while protected areas are shown
    if show_protected:
        st.info("Statistics shown only for peaks (disable 'Show Protected Areas').")

    else:
        if 'ele' in filtered_peaks.columns:
            # Histogram
            fig_hist = px.histogram(
                filtered_peaks,
                x='ele',
                nbins=30,
                labels={'ele': 'Elevation (m)', 'count': 'Number of Peaks'},
                title='Elevation Distribution'
            )
            fig_hist.update_layout(height=250, margin=dict(l=0, r=0, t=30, b=0), showlegend=False)
            st.plotly_chart(fig_hist, use_container_width=True)

            # Top 10 peaks
            st.markdown("**Top 10 Scores**")
            if 'name' in filtered_peaks.columns:
                top_peaks = filtered_peaks.nlargest(10, 'ele')[['name', 'ele']]
                top_peaks.columns = ['Peak Name', 'Elevation (m)']
                st.dataframe(top_peaks.reset_index(drop=True), use_container_width=True, hide_index=True, height=250)
            else:
                st.info("Peak names not available.")


#------------------------ELEVATION RANGE ANALYSIS-----------------------------
if 'ele' in filtered_peaks.columns:
    st.subheader("Scores by PLACEHOLDER Range")

    bins = [0, 1000, 2000, 3000, 4000, 5000]
    labels = ['<1000m', '1000-2000m', '2000-3000m', '3000-4000m', '>4000m']

    filtered_peaks['elevation_range'] = pd.cut(
        filtered_peaks['ele'],
        bins=bins,
        labels=labels,
        include_lowest=True
    )

    range_counts = filtered_peaks['elevation_range'].value_counts().sort_index()

    col1, col2 = st.columns(2)

    # bar chart
    with col1:
        fig_bar = px.bar(
            x=range_counts.index,
            y=range_counts.values,
            labels={'x': 'Elevation Range', 'y': 'Number of Peaks'},
            title='Peak Distribution by Elevation Range'
        )
        fig_bar.update_layout(height=350, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_bar, use_container_width=True)

    # pie chart
    with col2:
        fig_pie = px.pie(
            values=range_counts.values,
            names=range_counts.index,
            title='Percentage Distribution',
            hole=0.4
        )
        fig_pie.update_layout(height=350, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")

#------------------------DATA TABLE------------------------------------------
st.subheader("Score Details")

display_cols = ['latitude', 'longitude']
if 'name' in filtered_peaks.columns:
    display_cols.insert(0, 'name')
if 'ele' in filtered_peaks.columns:
    display_cols.append('ele')

display_df = filtered_peaks[display_cols].copy()
if 'ele' in display_df.columns:
    display_df['ele'] = display_df['ele'].round(0)

st.dataframe(display_df, use_container_width=True, hide_index=True, height=400)

#------------------------FOOTER----------------------------------------------
st.markdown("---")
st.markdown("*Data source: OpenStreetMap*")
