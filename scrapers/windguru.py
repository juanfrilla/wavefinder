from bs4 import BeautifulSoup
from typing import Dict
import pandas as pd
from utils import (
    rename_key,
    angle_to_direction,
    get_wind_status,
    render_html,
)
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
import streamlit as st


class Windguru(object):
    def __init__(self):
        pass

    def beach_request(self, browser, url):
        r_text = render_html(
            browser=browser, url=url, tag_to_wait="table.tabulka", timeout=60 * 1000
        )
        return BeautifulSoup(r_text, "html.parser")

    def format_forecast(self, forecast: Dict) -> Dict:
        forecast = rename_key(forecast, "tabid_0_0_dates", "datetime")
        forecast = rename_key(forecast, "tabid_0_0_SMER", "wind_direction")
        forecast = rename_key(forecast, "tabid_0_0_HTSGW", "wave_height")
        forecast = rename_key(forecast, "tabid_0_0_DIRPW", "wave_direction")
        forecast = rename_key(forecast, "tabid_0_0_PERPW", "wave_period")
        forecast = rename_key(forecast, "tabid_0_0_WINDSPD", "wind_speed")

        forecast["wind_direction"] = [
            angle_to_direction(self.parse_number_from_text(element))
            for element in forecast["wind_direction"]
        ]
        forecast["wave_direction"] = [
            angle_to_direction(self.parse_number_from_text(element))
            for element in forecast["wave_direction"]
        ]

        forecast["date"] = [
            self.datestr_to_backslashformat(dt.split(".")[0])
            for dt in forecast["datetime"]
        ]
        forecast["time"] = [
            dt.split(".")[1].replace("h", ":00") for dt in forecast["datetime"]
        ]
        del forecast["datetime"]

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
        self, soup: BeautifulSoup, url: str, index: int
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
                        value = cell.find("span")["title"]
                    else:
                        value = cell.get_text()
                    forecast[id].append(value)
        if forecast != {}:
            total_records = len(max(forecast.items(), key=lambda item: len(item[1]))[1])
            forecast["spot_name"] = self.parse_spot_names(soup, total_records)
            forecast = self.format_forecast(forecast)
            return pd.DataFrame(forecast)
        return pd.DataFrame()

    def process_soup(self, soup, url, index):
        df = self.get_dataframe_from_soup(soup, url, index)
        return self.format_dataframe(df)

    def parse_number_from_text(self, text):
        pattern = r"(\d+)°"

        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
        return None

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

    def format_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        # Hacerlo en menos lineas comprobando que la hora es de noche
        if not df.empty:
            df = df.drop(
                df[
                    (df["time"] == "03:00")
                    | (df["time"] == "04:00")
                    | (df["time"] == "05:00")
                    | (df["time"] == "21:00")
                    | (df["time"] == "22:00")
                ].index
            )
        return df

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

    def scrape(self, browser, url, index):
        soup = self.beach_request(browser, url)
        return self.process_soup(soup, url, index)
