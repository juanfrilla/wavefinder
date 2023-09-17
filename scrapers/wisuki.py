import requests
from bs4 import BeautifulSoup
from utils import (
    convert_all_values_of_dict_to_min_length,
    get_wind_status,
    angle_to_direction,
)
import pandas as pd
from datetime import datetime, timedelta
import re


class Wisuki(object):
    def __init__(self):
        self.headers = {
            "authority": "es.wisuki.com",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "es-ES,es;q=0.9",
            "cache-control": "max-age=0",
            "referer": "https://es.wisuki.com/region/442/lanzarote",
            "sec-ch-ua": '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        }

    def parse_number_from_title(self, title: str) -> int:
        pattern = r"\d+"

        match = re.search(pattern, title)

        if match:
            number_str = match.group()
            return int(number_str)
        else:
            raise Exception("No se ha encontrado numero en el titulo")

    # TODO comproabr si la lista que saca es la misma que la que te da wisuki
    def parse_formated_wind_direction(
        self, raw_wind_direction_tr: BeautifulSoup
    ) -> list:
        raw_wind_direction_tds = raw_wind_direction_tr.select("td > img")
        wind_directions = [
            self.parse_number_from_title(td["title"]) for td in raw_wind_direction_tds
        ]
        return self.angles_to_text(wind_directions)

    def parse_formated_waves_direction(self, wave_direction_tr: BeautifulSoup) -> list:
        raw_waves_direction_tds = wave_direction_tr.select("td > img")
        wind_directions = [
            self.parse_number_from_title(td["title"]) for td in raw_waves_direction_tds
        ]
        return self.angles_to_text(wind_directions)

    def parse_formated_wind_speed(self, raw_wind_speed_tr: BeautifulSoup) -> list:
        raw_wind_speed_tds = raw_wind_speed_tr.select("td")
        return [int(wind_speed.text) for wind_speed in raw_wind_speed_tds]

    def convert_angle_between_0_and_360(self, angle: int):
        if angle > 360:
            angle = angle - 360
        return angle

    def angles_to_text(self, angles: list) -> list:
        converted_angles = [
            self.convert_angle_between_0_and_360(angle) for angle in angles
        ]
        return [angle_to_direction(angle) for angle in converted_angles]

    def parse_formated_waves_height(self, soup: BeautifulSoup) -> list:
        raw_waves_height = soup.select("td")
        return [
            float(heigth.text) if heigth.text.strip() != "" else 0
            for heigth in raw_waves_height
        ]

    def parse_formated_waves_period(self, soup: BeautifulSoup) -> list:
        raw_periods = soup.select("td")
        return [int(raw_period.text) if raw_period.text.strip() != "" else 0 for raw_period in raw_periods]

    def parse_windstatus(self, wave_directions, wind_directions):
        return [
            get_wind_status(wind_dir, wave_dir)
            for wave_dir, wind_dir in zip(wave_directions, wind_directions)
        ]

    def parse_spot_name(self, soup):
        input = soup.select("title")[0].text.strip()
        pattern = r'en\s(.*?)\s\|\sWisuki'
        match = re.search(pattern, input)

        if match:
            return match.group(1)
        else:
            raise Exception("Pattern not found in the input string.")
    

    def parse_spot_names(self, spot_name, total_records):
        return [spot_name for _ in range(total_records)]

    def get_dataframe_from_soup(self, soup):
        data = self.obtain_data(soup)
        return pd.DataFrame(data)

    def process_soup(self, soup):
        df = self.get_dataframe_from_soup(soup)
        return self.format_dataframe(df)

    def format_dataframe(self, df):
        df = df.drop(
            df[
                (df["time"] == "01h") | (df["time"] == "04h") | (df["time"] == "22h")
            ].index
        )
        return df

    def parse_formated_dates(self, times: list) -> list:
        dates = []
        date = datetime.now().date()
        for index, time in enumerate(times):
            if (
                index - 1 > 0 and time < times[index - 1]
            ):  # and times[index + 1] < time:
                date += timedelta(days=1)
            date_str = datetime.strftime(date, "%d/%m/%Y")
            dates.append(date_str)
        return dates

    def parse_formated_time(self, soup: BeautifulSoup) -> list:
        raw_times = soup.select("tbody > tr")[0]
        times = []
        for time in raw_times:
            if time.text.strip() != "":
                times.append(time.text.strip())
        return times

    def parse_wind_rows(self, soup):
        return soup.select("tr.wind")

    def parse_wave_rows(self, soup):
        return soup.select("tr.waves")

    def obtain_data(self, soup):
        wind_rows = self.parse_wind_rows(soup)
        wave_rows = self.parse_wave_rows(soup)
        wind_directions = self.parse_formated_wind_direction(wind_rows[1])
        wind_speeds = self.parse_formated_wind_speed(wind_rows[2])
        wave_directions = self.parse_formated_waves_direction(wave_rows[1])
        waves_heigths = self.parse_formated_waves_height(wave_rows[2])
        waves_periods = self.parse_formated_waves_period(
            wave_rows[3]
        )  # este marca el tamaño de la lista
        times = self.parse_formated_time(soup)
        dates = self.parse_formated_dates(times)
        data = {
            "date": dates,
            "time": times,
            "wave_direction": wave_directions,
            "wind_direction": wind_directions,
            "wind_status": self.parse_windstatus(wave_directions, wind_directions),
            "wave_period": waves_periods,
            "wave_height": waves_heigths,
            "wind_speed": wind_speeds,
        }
        total_records = len(data["time"])
        data["spot_name"] = self.parse_spot_names(
            self.parse_spot_name(soup), total_records
        )
        data = convert_all_values_of_dict_to_min_length(data)
        return data

    def beach_request(self, url):
        response = requests.get(url=url, headers=self.headers)
        return BeautifulSoup(response.text, "html.parser")

    def scrape(self, url):
        soup = self.beach_request(url)
        return self.process_soup(soup)
