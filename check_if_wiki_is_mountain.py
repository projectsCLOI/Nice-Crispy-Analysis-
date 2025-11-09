import requests
import geopandas as gpd
from urllib.parse import quote
from tqdm import tqdm

# --- Settings ---
HEADERS = {"User-Agent": "TyrolPeaksBot/1.0 (contact: your_email@example.com)"}
LANG = "de"
TYROL_QID = "Q42880"  # Tyrol region
MOUNTAIN_QIDS = ["Q8502", "Q271669", "Q8072"]  # mountain, natural feature, volcano

# --- Load data ---
gdf = gpd.read_file("./Data/tyrol_peaks_wiki_seq.gpkg")

# Keep top 200 by Wikipedia views
gdf_top = gdf.sort_values("wikipedia_views", ascending=False).copy()

# --- Wikidata helper functions ---

def get_wikidata_entity(title, lang="de"):
    """Get Wikidata entity ID from a Wikipedia title."""
    url = f"https://{lang}.wikipedia.org/w/api.php?action=query&titles={quote(title)}&prop=pageprops&format=json"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        pages = r.json().get("query", {}).get("pages", {})
        return next(iter(pages.values())).get("pageprops", {}).get("wikibase_item")
    except Exception:
        return None


def check_mountain_and_tyrol(wikidata_id):
    """Check whether Wikidata entity is a mountain and located in Tyrol."""
    if not wikidata_id:
        return (False, False)

    url = f"https://www.wikidata.org/wiki/Special:EntityData/{wikidata_id}.json"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        entities = r.json().get("entities", {})
        entity = entities.get(wikidata_id, {})
        claims = entity.get("claims", {})

        is_mountain = False
        in_tyrol = False

        # P31 — instance of
        for c in claims.get("P31", []):
            if "datavalue" in c["mainsnak"]:
                qid = c["mainsnak"]["datavalue"]["value"]["id"]
                if qid in MOUNTAIN_QIDS:
                    is_mountain = True

        # P131 — located in administrative territorial entity
        for c in claims.get("P131", []):
            if "datavalue" in c["mainsnak"]:
                qid = c["mainsnak"]["datavalue"]["value"]["id"]
                if qid == TYROL_QID:
                    in_tyrol = True

        return (is_mountain, in_tyrol)

    except Exception:
        return (False, False)


# --- Run checks on top 200 peaks ---
wikidata_ids = []
is_mountain_flags = []
in_tyrol_flags = []

for _, row in tqdm(gdf_top.iterrows(), total=len(gdf_top)):
    name = row.get("name")
    if not name:
        wikidata_ids.append(None)
        is_mountain_flags.append(False)
        in_tyrol_flags.append(False)
        continue

    wikidata_id = get_wikidata_entity(name, lang=LANG)
    wikidata_ids.append(wikidata_id)

    is_mountain, in_tyrol = check_mountain_and_tyrol(wikidata_id)
    is_mountain_flags.append(is_mountain)
    in_tyrol_flags.append(in_tyrol)

# --- Add results ---
gdf_top["wikidata_id"] = wikidata_ids
gdf_top["is_mountain"] = is_mountain_flags
gdf_top["in_tyrol"] = in_tyrol_flags
gdf_filtered = gdf_top[(gdf_top["is_mountain"] == True) & (gdf_top["in_tyrol"] == True)].copy()
# --- Save results ---
gdf_filtered.to_file("top_tyrol_mountains.gpkg", driver="GPKG")

print(f"✅ Done: Saved Wikidata checks for {len(gdf_filtered)} peaks.")
print("📁 Output: tyrol_peaks_top200_wikidata.gpkg")
