import os
import json
import csv
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from atprototools import Session

with open('credentials.json') as f:
    creds = json.load(f)

BSKY_USERNAME = os.environ.get('BSKY_USERNAME') or creds.get("BSKY_USERNAME")
BSKY_PASSWORD = os.environ.get('BSKY_PASSWORD') or creds.get("BSKY_PASSWORD")
URL = "http://greatsalt.uslakes.info/Level.asp"
FILENAME = "levels.csv"
HEADERS = ['dt', 'water_level', 'timestamp_utc']

def scrape_water_level_info(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    water_level_info = soup.find('div', style=lambda value: 'font-size:46px' in value if value else False)
    water_level = float(water_level_info.text.strip().replace(",", ""))
    font_elements = soup.find_all('font')
    date_info = next((el for el in font_elements if re.search(r"\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday), \b", el.text)), None)
    time_info = next((el for el in font_elements if re.search(r"\b(?:[1-9]|1[0-2]):[0-5][0-9]:[0-5][0-9] [AP]M\b", el.text)), None)
    date = datetime.strptime(date_info.text.strip(), "%A, %B %d, %Y") if date_info is not None else None
    time = datetime.strptime(time_info.text.strip(), "%I:%M:%S %p") if time_info is not None else None
    dt = datetime.combine(date, time.time())
    return water_level, dt

def update_csv(filename, headers, dt, water_level):
    if not os.path.exists(filename) or os.stat(filename).st_size == 0:
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(headers)
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        data = list(reader)
        data = data[1:]
    timestamp_utc = datetime.utcnow().strftime("%Y-%m-%d_%H%M%S")
    data.append([dt.strftime("%Y-%m-%d_%H%M%S"), water_level, timestamp_utc])
    
    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(data)

def main():
    session = Session(BSKY_USERNAME, BSKY_PASSWORD)
    water_level, dt = scrape_water_level_info(URL)
    update_csv(FILENAME, HEADERS, dt, water_level)
    caption = f"Current water level of the Great Salt Lake: {water_level} feet MSL on {dt.strftime('%A, %B %d, %Y')} at {dt.strftime('%I:%M:%S %p')} MT."
    caption += "\n"
    # caption += "Source: http://greatsalt.uslakes.info/Level.asp"
    caption += "\n"
    caption += "A reminder: the Great Salt Lake is disappearing. Please consider getting involved to help save the lake: www.fogsl.org"
    resp = session.postBloot(caption)
    if resp.status_code == 200:
        print("Post created successfully!")
    else:
        print(f"Failed to create post: {resp.content}")

if __name__ == '__main__':
    main()