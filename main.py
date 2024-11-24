import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import pytz
import requests
from io import StringIO
from atprototools import Session

BSKY_USERNAME = os.getenv('BSKY_USERNAME')
BSKY_PASSWORD = os.getenv('BSKY_PASSWORD')

def get_data():
    now_mt = datetime.now(timezone.utc).astimezone(pytz.timezone('America/Denver'))
    url = (
        "https://nwis.waterdata.usgs.gov/usa/nwis/uv/"
        "?cb_62614=on&format=rdb&site_no=10010100&legacy=1"
        f"&begin_date={now_mt.year - 11}-{now_mt.month:02d}-{now_mt.day:02d}"
        f"&end_date={now_mt.year}-{now_mt.month:02d}-{now_mt.day:02d}"
    )
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        data_lines = response.text.split('\n')
        header_index = next(i for i, line in enumerate(data_lines) if line.startswith('agency_cd'))
        df = pd.read_table(StringIO('\n'.join(data_lines[header_index+1:])))
        df.columns = data_lines[header_index].split('\t')
        
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)
        
        water_level = df['144241_62614'].iloc[-1]
        latest_time = df.index[-1]
        df['dt_hours_from_latest'] = (df.index - latest_time).total_seconds() / 3600
        
        comparisons = {}
        for years_ago in [1, 2, 10]:
            try:
                target_date = latest_time.replace(year=latest_time.year - years_ago)
                df['time_diff'] = abs((df.index - target_date).total_seconds())
                closest_idx = df['time_diff'].idxmin()
                historical_level = df.loc[closest_idx, '144241_62614']
                
                diff = np.round(water_level - historical_level,2)
                period_str = f"{years_ago} year{'s' if years_ago > 1 else ''} ago"
                comparisons[period_str] = diff
                
            except IndexError:
                print(f"No data found for {years_ago} years ago")
        
        return latest_time, water_level, comparisons
        
    except Exception as e:
        print(f"Error fetching/processing data: {e}")
        raise

def get_emoji(comparison):
    if comparison > 0:
        return "⬆️"
    elif comparison < 0:
        return "⬇️"
    else:
        return ""

def main():
    try:
        session = Session(BSKY_USERNAME, BSKY_PASSWORD)
        current_time, water_level, comparisons = get_data()
        
        caption = [
            f"The current water level is {water_level} ft above mean sea level",
            "\nwhich compared with\n"
        ]
        
        for period, diff in comparisons.items():
            if not np.isnan(diff):
                if diff == 0:
                    direction = "equal"
                else:
                    direction = "higher" if diff > 0 else "lower"
                caption.append(f"{period} today is {abs(diff)} ft {direction} {get_emoji(diff)}")
        
        caption.append(f"\nas of {current_time.strftime('%A, %B %d, %Y')} at {current_time.strftime('%I:%M:%S %p')} MT")
        
        resp = session.postBloot('\n'.join(caption))
        print("Post created successfully!" if resp.status_code == 200 
              else f"Failed to create post: {resp.content}")
            
    except Exception as e:
        print(f"Error in main: {e}")
        raise

if __name__ == '__main__':
    main()