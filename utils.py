from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright

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


def render_html_from_browser(url, tag_to_wait=None, timeout=6000):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        page.goto(url)
        if tag_to_wait is not None:
            page.wait_for_selector(selector=tag_to_wait, timeout=timeout)
        html_content = page.content()
        context.close()
        browser.close()
    return html_content


def rename_key(dictionary, old_key, new_key):
    if old_key in dictionary:
        dictionary[new_key] = dictionary.pop(old_key)

    return dictionary


def final_format(df):
    df = df.drop(df[df["wind_status"] == "Onshore"].index)
    df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y")
    df["time"] = df["time"].str.extract("(\d+)").astype(int)
    df.sort_values(by=["date", "time", "spot_name"], ascending=[True, True, True])
    df["date"] = df["date"].dt.strftime("%d/%m/%Y")

    return df
