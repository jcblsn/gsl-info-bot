from atprototools import Session
from bs4 import BeautifulSoup
import requests, csv, os
from datetime import datetime, timedelta
import re

session = Session(BSKY_USERNAME, BSKY_PASSWORD)

url = "http://greatsalt.uslakes.info/Level.asp"
response = requests.get(url)

soup = BeautifulSoup(response.text, 'html.parser')

water_level_info = soup.find('div', style=lambda value: 'font-size:46px' in value if value else False)
water_level = float(water_level_info.text.strip().replace(",", ""))

font_elements = soup.find_all('font')
date_info = next((el for el in font_elements if re.search(r"\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday), \b", el.text)), None)
time_info = next((el for el in font_elements if re.search(r"\b(?:[1-9]|1[0-2]):[0-5][0-9]:[0-5][0-9] [AP]M\b", el.text)), None)
if date_info is not None:
    date = datetime.strptime(date_info.text.strip(), "%A, %B %d, %Y")
if time_info is not None:
    time = datetime.strptime(time_info.text.strip(), "%I:%M:%S %p")
date = datetime.strptime(date_info.text.strip(), "%A, %B %d, %Y")
time = datetime.strptime(time_info.text.strip(), "%I:%M:%S %p")
dt = datetime.combine(date, time.time())

filename = "levels.csv"
headers = ['dt', 'water_level', 'timestamp']

if not os.path.exists(filename) or os.stat(filename).st_size == 0:
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)

with open(filename, 'r') as file:
    reader = csv.reader(file)
    data = list(reader)
    data = data[1:]

day_change = week_change = month_change = "N/A"
for row in data:
    row_date = datetime.strptime(row[0], "%Y-%m-%d_%H%M%S")
    if row_date == date - timedelta(days=1):
        day_change = water_level - float(row[1])
    # elif row_date == date - timedelta(days=7):
    #     week_change = water_level - float(row[1])
    # elif row_date == date - timedelta(days=30):
    #     month_change = water_level - float(row[1])

timestamp_utc = datetime.utcnow().strftime("%Y-%m-%d_%H%M%S")
data.append([dt.strftime("%Y-%m-%d_%H%M%S"), water_level, timestamp_utc])
with open(filename, "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerows(data)

caption = f"Current water level of the Great Salt Lake: {water_level} feet MSL on {date.strftime('%A, %B %d, %Y')} at {time.strftime('%I:%M:%S %p')} MT."
caption += f"\n\nChange from yesterday: {day_change} feet.\n\nChange from last week: {week_change} feet.\n\nChange from last month: {month_change} feet."
caption += f"\n\nSource: http://greatsalt.uslakes.info/Level.asp"
resp = session.postBloot(caption)

if resp.status_code == 200:
    print("Post created successfully!")
else:
    print(f"Failed to create post: {resp.content}")