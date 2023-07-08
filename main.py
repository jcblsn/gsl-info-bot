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
import pytz
from atprototools import Session

if os.path.exists('credentials.json'):
    with open('credentials.json') as f:
        creds = json.load(f)
    BSKY_USERNAME = creds.get("BSKY_USERNAME")
    BSKY_PASSWORD = creds.get("BSKY_PASSWORD")
else:
    BSKY_USERNAME = os.environ.get('BSKY_USERNAME')
    BSKY_PASSWORD = os.environ.get('BSKY_PASSWORD')

def get_data():
    
    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
    now_mt = now_utc.astimezone(pytz.timezone('America/Denver'))
    
    past_10_years_url = f"https://nwis.waterdata.usgs.gov/usa/nwis/uv/?cb_62614=on&format=rdb&site_no=10010100&legacy=1&period=&begin_date={now_mt.year - 10}-{now_mt.month:02d}-{now_mt.day:02d}&end_date={now_mt.year}-{now_mt.month:02d}-{now_mt.day:02d}"
    
    history = pd.read_table(past_10_years_url, sep='\t',skiprows=28)
    history = history[[i[5:10] == now_mt.strftime("%m-%d") for i in history['datetime']]]
    
    history['year'] = [i[:4] for i in history['datetime']]
    history['date_without_time'] = [i[:10] for i in history['datetime']]
    
    dt = history.tail(1)['datetime'].to_numpy()[0]
    dt = datetime.strptime(dt, "%Y-%m-%d %H:%M")
    water_level = history.tail(1)['144241_62614'].to_numpy()[0]

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
    
    return dt, water_level, comparison

def get_emoji(comparison):
    if comparison > 0:
        return "higher ⬆️"
    elif comparison < 0:
        return "lower ⬇️"
    else:
        return ""

def main():
    session = Session(BSKY_USERNAME, BSKY_PASSWORD)
    dt, water_level, comparison = get_data()
    caption = f"The current water level is {water_level} ft above mean sea level"
    caption += "\n\nwhich compared with"
    caption += "\n\n1 year ago today is {} ft {}\n2 years ago today is {} ft {}\n10 years ago today is {} ft {}".format(
        abs(comparison["1 year ago"]), get_emoji(comparison["1 year ago"]),
        abs(comparison["2 years ago"]), get_emoji(comparison["2 years ago"]),
        abs(comparison["10 years ago"]), get_emoji(comparison["10 years ago"])
    )
    caption += f"\n\nas of {dt.strftime('%A, %B %d, %Y')} at {dt.strftime('%I:%M:%S %p')} MT"
    print(caption)
    resp = session.postBloot(caption)
    if resp.status_code == 200:
        print("Post created successfully!")
    else:
        print(f"Failed to create post: {resp.content}")

if __name__ == '__main__':
    main()