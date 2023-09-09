from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, date, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import numpy as np

MONTH_MAPPING = {
    "Ene": "01",
    "Feb": "02",
    "Mar": "03",
    "Abr": "04",
    "May": "05",
    "Jun": "06",
    "Jul": "07",
    "Ago": "08",
    "Sep": "09",
    "Oct": "10",
    "Nov": "11",
    "Dic": "12",
}
INTERNAL_DATE_STR_FORMAT = "%d/%m/%Y"
INTERNAL_TIME_STR_FORMAT = "%H:%M:%S"


def get_wind_status(wind_direction, wave_direction):
    if is_offshore(wind_direction, wave_direction):
        return "Offshore"
    elif is_crossoff(wind_direction, wave_direction):
        return "Cross-off"
    else:
        return "Onshore"


def angle_to_direction(angle):
    angle %= 360

    if 0 <= angle < 22.5 or angle >= 337.5:
        return "North"
    elif 22.5 <= angle < 67.5:
        return "NorthEast"
    elif 67.5 <= angle < 112.5:
        return "East"
    elif 112.5 <= angle < 157.5:
        return "SouthEast"
    elif 157.5 <= angle < 202.5:
        return "South"
    elif 202.5 <= angle < 247.5:
        return "SouthWest"
    elif 247.5 <= angle < 292.5:
        return "West"
    elif 292.5 <= angle < 337.5:
        return "NorthWest"


def is_offshore(wind_direction, wave_direction):
    if wind_direction == "North" and wave_direction == "South":
        return True
    elif wind_direction == "South" and wave_direction == "North":
        return True
    elif wind_direction == "East" and wave_direction == "West":
        return True
    elif wind_direction == "West" and wave_direction == "East":
        return True
    elif wind_direction == "NorthEast" and wave_direction == "SouthWest":
        return True
    elif wind_direction == "SouthWest" and wave_direction == "NorthEast":
        return True
    elif wind_direction == "NorthWest" and wave_direction == "SouthEast":
        return True
    elif wind_direction == "SouthEast" and wave_direction == "NorthWest":
        return True
    else:
        return False


def is_crossoff(wind_direction, wave_direction):
    if wave_direction == "North" and wind_direction == "SouthEast":
        return True
    elif wave_direction == "North" and wind_direction == "SouthWest":
        return True
    elif wave_direction == "South" and wind_direction == "NorthEast":
        return True
    elif wave_direction == "South" and wind_direction == "NorthWest":
        return True
    elif wave_direction == "East" and wind_direction == "NorthWest":
        return True
    elif wave_direction == "East" and wind_direction == "SouthWest":
        return True
    elif wave_direction == "West" and wind_direction == "NorthEast":
        return True
    elif wave_direction == "West" and wind_direction == "SouthEast":
        return True
    elif wave_direction == "NorthEast" and wind_direction == "South":
        return True
    elif wave_direction == "NorthWest" and wind_direction == "South":
        return True
    elif wave_direction == "SouthEast" and wind_direction == "North":
        return True
    elif wave_direction == "SouthWest" and wind_direction == "North":
        return True
    elif wave_direction == "NorthEast" and wind_direction == "West":
        return True
    elif wave_direction == "SouthEast" and wind_direction == "West":
        return True
    elif wave_direction == "NorthWest" and wind_direction == "East":
        return True
    elif wave_direction == "SouthWest" and wind_direction == "East":
        return True
    else:
        return False


def export_to_html(filename, soup: BeautifulSoup):
    # Export the BeautifulSoup content to an HTML file
    with open(filename, "w") as file:
        file.write(soup.prettify())


def import_html(filename):
    with open(filename, "r") as file:
        return file.read()


def combine_df(df1, df2):
    df = pd.concat([df1, df2], axis=0, ignore_index=True)
    return df


def convert_datestr_format(datestr):
    # Define the mapping of month names to their numeric representations

    day = int(datestr.split(" ")[-1].strip())
    month_name = datestr.split(" ")[-2].strip()
    month = MONTH_MAPPING[month_name]
    current_year = datetime.now().year

    date_obj = datetime(current_year, int(month), day)

    return date_obj.strftime("%d/%m/%Y")


def open_browser():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    browser = webdriver.Chrome(options=options)
    return browser


def render_html(browser, url, tag_to_wait=None, timeout=10):
    browser.get(url)
    if tag_to_wait:
        WebDriverWait(browser, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, tag_to_wait))
        )
    html_content = browser.page_source
    return html_content


def rename_key(dictionary, old_key, new_key):
    if old_key in dictionary:
        dictionary[new_key] = dictionary.pop(old_key)

    return dictionary


def get_day_name(days_to_add: float) -> str:
    today = date.today()
    day = today + timedelta(days=days_to_add)
    day_name_number = day.strftime("%m-%d, %A")

    return day_name_number


def final_format(df):
    df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y")
    df.sort_values(by=["date", "time", "spot_name"], ascending=[True, True, True])
    df["date"] = df["date"].dt.strftime("%d/%m/%Y")

    df = df[
        [
            "date",
            "time",
            "spot_name",
            "wind_status",
            "wave_height",
            "wave_period",
            "wind_direction",
            "wave_direction",
            "wind_speed"
        ]
    ]
    return df


def degrees_to_direction(degrees):
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    index = round(degrees / 45) % 8
    return directions[index]


def classify_wind_speed(speed_knots):
    if speed_knots < 1:
        return "Calm"
    elif speed_knots <= 3:
        return "Light Air"
    elif speed_knots <= 7:
        return "Light Breeze"
    elif speed_knots <= 12:
        return "Gentle Breeze"
    elif speed_knots <= 18:
        return "Moderate Breeze"
    elif speed_knots <= 24:
        return "Fresh Breeze"
    elif speed_knots <= 31:
        return "Strong Breeze"
    elif speed_knots <= 38:
        return "High Wind, Moderate Gale, Near Gale"
    elif speed_knots <= 46:
        return "Gale, Fresh Gale"
    elif speed_knots <= 54:
        return "Strong Gale"
    elif speed_knots <= 63:
        return "Storm, Whole Gale"
    elif speed_knots <= 72:
        return "Violent Storm"
    else:
        return "Hurricane"


def feet_to_meters(feet):
    meters = feet * 0.3048
    return meters


def datetime_to_str(dt: datetime, dt_format: str) -> str:
    return dt.strftime(dt_format)


def timestamp_to_datetime(timestamp_date: int) -> datetime:
    return datetime.utcfromtimestamp(timestamp_date)


def add_offset_to_datetime(dt: datetime, utc_offset: int) -> datetime:
    return dt + timedelta(hours=utc_offset)


def timestamp_to_datetimestr(timestamp_date: int, utc_offset: int) -> str:
    datetime_dt = timestamp_to_datetime(timestamp_date)
    datestr = datetime_to_str(
        add_offset_to_datetime(datetime_dt, utc_offset), INTERNAL_DATE_STR_FORMAT
    )
    timestr = datetime_to_str(
        add_offset_to_datetime(datetime_dt, utc_offset), INTERNAL_TIME_STR_FORMAT
    )
    return datestr, timestr


def str_to_datetime(dtstr) -> datetime:
    return datetime.strptime(dtstr, INTERNAL_DATE_STR_FORMAT)


def get_datename(dt: str):
    dt_dt = str_to_datetime(dt).date()

    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    day_after_tomorrow = today + timedelta(days=2)

    if dt_dt == today:
        return "Today"
    elif dt_dt == tomorrow:
        return "Tomorrow"
    elif dt_dt == day_after_tomorrow:
        return "Day After Tomorrow"
    else:
        return "Another Day"
