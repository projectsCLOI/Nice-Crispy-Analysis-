import geopandas as gpd
import requests
import json
import time

ACCESS_TOKEN = '936d81f88312c1d058de5c6a069b963c5d7fb619'
GPKG_PATH = 'top_tyrol_mountains.gpkg'
LAYER_NAME = 'top_tyrol_mountains'
BUFFER_DISTANCE = 0.02  # degrees ~ 1 km if using lat/lng

BASE_URL = 'https://www.strava.com/api/v3'
HEADERS = {'Authorization': f'Bearer {ACCESS_TOKEN}'}

def get_bounding_box(point, buffer_distance):
    """
    Returns bounding box coordinates of a buffered point geometry.
    This creates a square region around each mountain to search nearby Strava segments.
    """
    buffered = point.buffer(buffer_distance)
    return buffered.bounds  #returns (minx, miny, maxx, maxy)

def explore_segments(bounds_tuple, max_retries=3):
    """
    Calls Strava's segment explore API for a bounding box.
    Handles rate limits by retrying automatically if needed.
    Returns a list of found segment IDs within the bounding box.
    """
    minx, miny, maxx, maxy = bounds_tuple
    bounds_str = f"{miny},{minx},{maxy},{maxx}"  #lat_sw, lon_sw, lat_ne, lon_ne
    params = {'bounds': bounds_str}

    url = f'{BASE_URL}/segments/explore'
    retries = 0
    while retries < max_retries:
        response = requests.get(url, headers=HEADERS, params=params)
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 15))
            print(f"Rate limit hit for explore_segments. Sleeping for {retry_after} seconds.")
            time.sleep(retry_after)
            retries += 1
        else:
            try:
                response.raise_for_status()
                data = response.json()
                return [segment['id'] for segment in data.get('segments', [])]
            except requests.HTTPError as e:
                print(f"HTTP error in explore_segments: {e}")
                break
    print("Max retries reached for explore_segments")
    return []

def get_segment_details_with_retry(segment_id, max_retries=3):
    """
    Fetches detailed info about a Strava segment by its ID.
    Handles rate limits automatically. Returns a dictionary (segment data).
    """
    url = f'{BASE_URL}/segments/{segment_id}'
    retries = 0
    while retries < max_retries:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 15))
            print(f"Rate limit hit for segment {segment_id}. Sleeping for {retry_after} seconds.")
            time.sleep(retry_after)
            retries += 1
        else:
            try:
                response.raise_for_status()
                return response.json()
            except requests.HTTPError as e:
                print(f"HTTP error fetching segment {segment_id}: {e}")
                break
    print(f"Max retries reached for segment {segment_id}")
    return None

if __name__ == '__main__':
    gdf = gpd.read_file(GPKG_PATH, layer=LAYER_NAME)
    all_segment_ids = set()
    all_details = []

    #for each mountain point
    for idx, row in gdf.iterrows():
        point = row.geometry #getting geographic point of mountain location
        bbox = get_bounding_box(point, BUFFER_DISTANCE) #creating the bounding box 

        ids = explore_segments(bbox)
        for segment_id in ids:
            if segment_id not in all_segment_ids:
                details = get_segment_details_with_retry(segment_id)
                if details:
                    all_details.append(details)
                    all_segment_ids.add(segment_id)
                time.sleep(2)  #2 second delay between detail requests to reduce rate limit risk

    #saving all segments detail responses to JSON file
    with open('segments2.json', 'w') as f:
        json.dump(all_details, f, indent=4)

    print(f"Saved {len(all_details)} segment details to segments.json")
