import os
import json
import csv
import re
import requests
from io import StringIO
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from atprototools import Session

# https://nwis.waterdata.usgs.gov/usa/nwis/uv/?cb_62614=on&format=rdb&site_no=10010100&legacy=1&period=&begin_date=2018-07-06&end_date=2023-07-06

if os.path.exists('credentials.json'):
    with open('credentials.json') as f:
        creds = json.load(f)
    BSKY_USERNAME = creds.get("BSKY_USERNAME")
    BSKY_PASSWORD = creds.get("BSKY_PASSWORD")
else:
    BSKY_USERNAME = os.environ.get('BSKY_USERNAME')
    BSKY_PASSWORD = os.environ.get('BSKY_PASSWORD')

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
    
    with open(filename, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(data)

def compare_with_previous_years(water_level, dt):
    
    past_10_years_url = f"https://nwis.waterdata.usgs.gov/usa/nwis/uv/?cb_62614=on&format=rdb&site_no=10010100&legacy=1&period=&begin_date={dt.year - 10}-{dt.month:02d}-{dt.day:02d}&end_date={dt.year}-{dt.month:02d}-{dt.day:02d}"
    
    history = pd.read_table(past_10_years_url, sep='\t',skiprows=28)
    history = history.iloc[1:]
    
    history['year'] = [i[:4] for i in history['datetime']]
    history['date_without_time'] = [i[:10] for i in history['datetime']]
    
    last_year = dt.year - 1
    two_years_ago = dt.year - 2
    ten_years_ago = dt.year - 10
    
    today_without_year = dt.strftime("%m-%d")
    
    water_level_1_year_ago = history[(history['year'] == str(last_year)) & [i[5:] == today_without_year for i in history['date_without_time']]]['144241_62614'].astype(float).mean()
    water_level_2_years_ago = history[(history['year'] == str(two_years_ago)) & [i[5:] == today_without_year for i in history['date_without_time']]]['144241_62614'].astype(float).mean()
    water_level_10_years_ago = history[(history['year'] == str(ten_years_ago)) & [i[5:] == today_without_year for i in history['date_without_time']]]['144241_62614'].astype(float).mean() 
    
    comparison = {
        "1 year ago": np.nan if np.isnan(water_level_1_year_ago) else (water_level - water_level_1_year_ago).round(2),
        "2 years ago": np.nan if np.isnan(water_level_2_years_ago) else (water_level - water_level_2_years_ago).round(2),
        "10 years ago": np.nan if np.isnan(water_level_10_years_ago) else (water_level - water_level_10_years_ago).round(2)
    }
    
    return comparison

def get_emoji(comparison):
    if comparison > 0:
        return "higher ⬆️"
    elif comparison < 0:
        return "lower ⬇️"
    else:
        return ""

def main():
    session = Session(BSKY_USERNAME, BSKY_PASSWORD)
    water_level, dt = scrape_water_level_info(URL)
    comparison = compare_with_previous_years(water_level, dt)
    update_csv(FILENAME, HEADERS, dt, water_level)
    caption = f"The current water level is {water_level} ft above mean sea level"
    caption += "\n\nwhich compared with"
    caption += "\n\n1 year ago is {} ft {}\n2 years ago is {} ft {}\n10 years ago is {} ft {}".format(
        # absolute value
        abs(comparison["1 year ago"]), get_emoji(comparison["1 year ago"]),
        abs(comparison["2 years ago"]), get_emoji(comparison["2 years ago"]),
        abs(comparison["10 years ago"]), get_emoji(comparison["10 years ago"])
    )
    caption += f"\n\nas of {dt.strftime('%A, %B %d, %Y')} at {dt.strftime('%I:%M:%S %p')} MT"
    # caption += "\n\nA reminder: the Great Salt Lake is disappearing. Please consider getting involved with conservation efforts at www.fogsl.org"
    print(caption)
    resp = session.postBloot(caption)
    if resp.status_code == 200:
        print("Post created successfully!")
    else:
        print(f"Failed to create post: {resp.content}")

if __name__ == '__main__':
    main()