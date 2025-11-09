import csv
import json
from datetime import date, timedelta

from ultralytics import YOLO

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

from tqdm import tqdm

model = YOLO("yolo11l.pt")

def get_coordinates_for_webcam(html_content:str):
    # Parse the HTML
    soup = BeautifulSoup(html_content, "html.parser")

    # Find all JSON-LD scripts
    scripts = soup.find_all("script", type="application/ld+json")

    latitude = longitude = None

    for script in scripts:
        try:
            data = json.loads(script.string)
            # Check if this script has the geo coordinates
            if 'locationCreated' in data:
                data = data['locationCreated']
            if "geo" in data :
                geo = data["geo"]
                latitude = geo.get("latitude")
                longitude = geo.get("longitude")
                break  # Stop after finding the first one
        except (json.JSONDecodeError, TypeError):
            continue

    return (longitude, latitude)


def get_webcam_ids(base_url):
    response = requests.get(base_url)
    webcam_pages = []
    if response.status_code==200:
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all links ending with '/webcams/'
        for el in soup.find_all('li', {"class": "hastotals"}):
            for a in el.find_all('a', href=True):
                href = a['href']

                if href.endswith('/webcams/') and href.startswith('/sommer'):
                    some_url = urljoin(base_url, href)
                    webcam_pages.append(some_url)
    all_ids = dict()

    for webcam_page in webcam_pages:
        print(f"Scraping webcams from: {webcam_page}")
        res = requests.get(webcam_page)
        if res.status_code == 200:
            page_soup = BeautifulSoup(res.text, 'html.parser')

            # Find all webcam IDs like /webcams/c1078/
            for a in page_soup.find_all('a', href=True):
                match = re.search(r'/webcams/(c\d+)/', a['href'])
                if match:
                    response = requests.get('https://www.bergfex.at' + a['href'])
                    all_ids[match.group(1)] = get_coordinates_for_webcam(response.text) if response.status_code == 200 else None


    return all_ids

def get_webcam_images(webcam_id, webcam_date):
    #date str format = 2025-11-06
    date_str = webcam_date.strftime('%Y-%m-%d')
    response = requests.get(f"https://images.bergfex.at/ajax/webcamsarchive/?id={webcam_id}&date={date_str}&size=6")
    if response.status_code == 200:
        return json.loads(response.content) or {}
    else:
        return {}

def classify_images(image_paths: list[str]):
    results = model.predict(source=image_paths, conf=0.35)
    num_persons = [x.boxes.cls.tolist().count(0) for x in results]
    num_cars = [x.boxes.cls.tolist().count(2) for x in results]
    num_bicycle = [x.boxes.cls.tolist().count(1) for x in results]
    # for idx, detections in enumerate(num_persons):
    #     if detections:
    #         results[idx].show()  # display to screen
    #         results[idx].save(filename="result.jpg")  # save to disk
    return {"persons": num_persons, "cars": num_cars, "bicycle": num_bicycle}


if __name__ == '__main__':
    base_url = "https://www.bergfex.at/sommer/tirol/webcams/"
    webcam_ids = get_webcam_ids(base_url)
    with open("webcam_ids.txt", "w") as f:
        f.write("\n".join(webcam_ids))
    current_day = date.today()
    webcam_images = {}
    webcam_detections = {}

    for webcam_id, coords in tqdm(webcam_ids.items()):
        print(webcam_id)
        images = []
        for i in range(7):
            this_day = date.today() - timedelta(days=i)
            images.extend(get_webcam_images(webcam_id[1:], this_day))
        webcam_images[webcam_id] = images

        classification_results = classify_images([x["src"] for x in images]) if images else {"persons": [0], "cars": [0], "bicycle": [0]}
        num_ppl =  sum(classification_results["persons"])
        with open("Data/ppl_on_mountains_tyrol.csv", "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([coords, num_ppl, webcam_id])



    print()
