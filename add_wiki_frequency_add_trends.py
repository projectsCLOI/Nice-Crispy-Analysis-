import pandas as pd
import requests
import geopandas as gpd
from pytrends.request import TrendReq
from tqdm import tqdm
from urllib.parse import quote

# Load your previously downloaded Tyrol peaks GeoDataFrame
# gdf = gpd.read_file("tyrol_osm_protected_areas.gpkg")
# Or your specific peaks GeoDataFrame
# Make sure it has a 'name' column

peaks_gdf = gpd.read_file("./Data/tyrol_mountain_peaks.gpkg")

# Limit number of peaks to query (avoid API overload)
#LIMIT = 20
#peaks_gdf = peaks_gdf.head(LIMIT)

# --- 1️⃣ Wikipedia Pageviews ---
import time
import requests
import geopandas as gpd
from urllib.parse import quote
from tqdm import tqdm

# Optional: limit for testing
# gdf = gdf.head(100)

# --- Wikipedia API setup ---
HEADERS = {"User-Agent": "TyrolPeaksBot/1.0 (contact: your_email@example.com)"}
LANG = "de"
START = "20250101"
END = "20251101"
BATCH_SIZE = 20  # number of requests before sleeping

def get_wikipedia_views(peak_name):
    """
    Fetch total Wikipedia pageviews for a given peak.
    Returns None if not found or forbidden.
    """
    if not peak_name:
        return None
    url = (
        "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
        f"{LANG}.wikipedia/all-access/all-agents/{quote(peak_name.replace(' ', '_'))}/daily/{START}/{END}"
    )
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code in (403, 404):
            return None
        r.raise_for_status()
        data = r.json()
        print(data)
        items = data.get("items", [])
        if len(items) > 0:
            return sum(item["views"] for item in items)
        else:
            return None
    except Exception:
        return None


# --- Main loop with 20-request throttling ---
results = []
for i, row in tqdm(enumerate(peaks_gdf.itertuples()), total=len(peaks_gdf)):
    peak_name = getattr(row, "name", None)
    views = get_wikipedia_views(peak_name)
    results.append(views)

    # After every 20 requests, sleep for 1 second
    if (i + 1) % BATCH_SIZE == 0:
        time.sleep(1)

# --- Save results ---
peaks_gdf["wikipedia_views"] = results
peaks_gdf = peaks_gdf[peaks_gdf["wikipedia_views"].notnull()]
peaks_gdf.to_file("tyrol_peaks_wiki_seq.gpkg", driver="GPKG")

if False:
    print(f"✅ Done: Wikipedia data saved for {len(gdf)} peaks.")

    # --- 2️⃣ Google Trends (optional) ---
    pytrends = TrendReq(hl="en-US", tz=360)

    # Google Trends limits max 5 keywords per request
    MAX_GT_KEYWORDS = 5
    peaks_gdf["google_trend_index"] = None

    for i in range(0, len(peaks_gdf), MAX_GT_KEYWORDS):
        batch = peaks_gdf.iloc[i:i+MAX_GT_KEYWORDS]
        keywords = [str(n) + " Tirol" for n in batch["name"] if pd.notna(n)]
        if not keywords:
            continue
        try:
            print(keywords)
            pytrends.build_payload(keywords, timeframe="today 12-m")
            trend_df = pytrends.interest_over_time()
            # Take mean index over last 12 months
            mean_index = trend_df[keywords].mean()
            print(trend_df)
            peaks_gdf.loc[batch.index, "google_trend_index"] = mean_index.values
        except Exception:
            continue

    # --- 3️⃣ Save enriched GeoDataFrame ---
    peaks_gdf.to_file("tyrol_peaks_enriched.gpkg", driver="GPKG")
    print(f"✅ Enriched {len(peaks_gdf)} peaks saved to 'tyrol_peaks_enriched.gpkg'")