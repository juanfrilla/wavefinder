from bs4 import BeautifulSoup
from typing import Dict
import polars as pl
from utils import (
    rename_key,
    angle_to_direction,
    get_wind_status,
    render_html,
)
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta


class Windguru(object):
    def __init__(self):
        pass

    def beach_request(self, url):
        r_text = render_html(url=url, tag_to_wait="table.tabulka", timeout=60 * 1000)
        return BeautifulSoup(r_text, "html.parser")

    def format_forecast(self, forecast: Dict) -> Dict:
        forecast = rename_key(forecast, "tabid_0_0_dates", "datetime")
        forecast = rename_key(forecast, "tabid_0_0_SMER", "wind_direction")
        forecast = rename_key(forecast, "tabid_0_0_HTSGW", "wave_height")
        forecast = rename_key(forecast, "tabid_0_0_DIRPW", "wave_direction")
        forecast = rename_key(forecast, "tabid_0_0_PERPW", "wave_period")
        forecast = rename_key(forecast, "tabid_0_0_WINDSPD", "wind_speed")

        forecast["wind_direction"] = [
            self.parse_text_from_text(element) for element in forecast["wind_direction"]
        ]
        forecast["wave_direction"] = [
            self.parse_text_from_text(element) for element in forecast["wave_direction"]
        ]

        forecast["date"] = [
            self.datestr_to_backslashformat(dt.split(".")[0])
            for dt in forecast["datetime"]
        ]
        forecast["time"] = [
            dt.split(".")[1].replace("h", ":00") for dt in forecast["datetime"]
        ]
        forecast["datetime"] = [
            datetime.strptime(f"{date} {time}", "%d/%m/%Y %H:%M")
            for date, time in zip(forecast["date"], forecast["time"])
        ]
        del forecast["date"]
        del forecast["time"]

        forecast["wind_status"] = self.parse_windstatus(
            forecast["wave_direction"], forecast["wind_direction"]
        )
        forecast["wave_period"] = self.format_dict_digit_all_values(
            forecast, "wave_period", "int"
        )
        forecast["wave_height"] = self.format_dict_digit_all_values(
            forecast, "wave_height", "float"
        )
        forecast["wind_speed"] = self.format_dict_digit_all_values(
            forecast, "wind_speed", "float"
        )
        return forecast

    def parse_spot_name(self, soup):
        return soup.select("div.spot-name.wg-guide")[0].text.strip()

    def parse_spot_names(self, soup, total_records):
        return [self.parse_spot_name(soup) for _ in range(total_records)]

    def get_dataframe_from_soup(
        self,
        soup: BeautifulSoup,
    ) -> Dict:
        forecast = {}
        table = soup.find("table", class_="tabulka")
        tablebody = table.find("tbody")
        rows = tablebody.find_all("tr")

        for row in rows:
            cells = row.find_all("td")
            id = row["id"]
            if id in [
                "tabid_0_0_SMER",
                "tabid_0_0_dates",
                "tabid_0_0_HTSGW",
                "tabid_0_0_DIRPW",
                "tabid_0_0_PERPW",
                "tabid_0_0_WINDSPD",
            ]:
                forecast[id] = []
                for cell in cells:
                    if ("SMER" in id) | ("DIRPW" in id):
                        value = cell.find("span")["title"].replace("W", "O")
                    else:
                        value = cell.get_text()
                    forecast[id].append(value)
        if forecast != {}:
            total_records = len(max(forecast.items(), key=lambda item: len(item[1]))[1])
            forecast["spot_name"] = self.parse_spot_names(soup, total_records)
            forecast = self.format_forecast(forecast)
            return pl.DataFrame(forecast)
        return pl.DataFrame()

    def parse_number_from_text(self, text):
        pattern = r"(\d+)°"

        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
        return None

    def parse_text_from_text(self, text):
        return text.split(" ")[0]

    def parse_windstatus(self, wave_directions, wind_directions):
        return [
            get_wind_status(wind_dir, wave_dir)
            for wave_dir, wind_dir in zip(wave_directions, wind_directions)
        ]

    def format_dict_digit_all_values(self, forecast, forecast_value, digit_type):
        if digit_type == "int":
            return [
                int(forecast[forecast_value][i])
                for i in range(len(forecast[forecast_value]))
            ]
        elif digit_type == "float":
            return [
                float(forecast[forecast_value][i])
                for i in range(len(forecast[forecast_value]))
            ]

    def datestr_to_backslashformat(self, input_text):
        # si es menor es del próximo mes, si es mayor o igual es de este mes
        day = re.search(r"\d+", input_text).group()

        current_date = datetime.now()

        if int(day) < current_date.day:
            new_date = current_date + relativedelta(months=1)
            month = new_date.month
        elif int(day) >= current_date.day:
            month = current_date.month
        year = current_date.year

        date_datetime = datetime.strptime(f"{day}/{month}/{year}", "%d/%m/%Y")

        return date_datetime.strftime("%d/%m/%Y")

    def scrape(self, url):
        soup = self.beach_request(url)
        df = self.get_dataframe_from_soup(soup)
        return self.get_dataframe_from_soup(soup)
