from bs4 import BeautifulSoup
import requests
import pandas as pd
from utils import rename_key
from datetime import datetime, timedelta
import numpy as np
import re


class SurfForecast(object):
    def __init__(self):
        self.headers = {
            "authority": "www.surf-forecast.com",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "es-ES,es;q=0.9",
            "cache-control": "max-age=0",
            "if-none-match": 'W/"d86aa45153cc2e059ce6221affec67a7"',
            "sec-ch-ua": '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        }

    def beach_request(self, url):
        response = requests.get(
            url=url,
            headers=self.headers,
        )

        return response

    # TODO escrapear dias y no añadirlos asi
    def add_days_to_forecast(self, forecast):
        time_list = forecast["time"]
        days_list = []
        date = datetime.now()
        for index, time in enumerate(time_list):
            if time == "AM" and index != 0:
                date += timedelta(days=1)
                days_list.append(date.strftime("%d/%m/%Y"))
            else:
                days_list.append(date.strftime("%d/%m/%Y"))
        forecast["date"] = days_list
        return forecast

    def parse_spot_name(self, soup):
        return soup.find_all("option", selected=True)[3].text

    def parse_spot_names(self, spot_name, total_records):
        return [spot_name for _ in range(total_records)]

    def get_formatted_wind_status(self, forecast):
        new_wind_status = []
        translator = {
            "on": "Onshore",
            "off": "Offshore",
            "cross": "Crossshore",
            "cross-off": "Cross-off",
            "cross-on": "Cross-on",
        }
        for element in forecast["wind_status"]:
            new_wind_status.append(translator[element])
        return new_wind_status

    def get_formatted_wave_height(self, forecast):
        new_wave_height = []
        pattern = r"(\d+(\.\d+)?)"
        for element in forecast["wave_height"]:
            match = re.match(pattern, element)
            if match:
                numeric_value = float(match.group(1))
                new_wave_height.append(numeric_value)
        return new_wave_height

    def get_dataframe_from_soup(self, soup):
        forecast = {}
        spot_name = self.parse_spot_name(soup)
        drn_list = [
            "time",
            "wave-height",
            "periods",
            "energy",
            "wind",
            "wind-state",
        ]
        for row_name in drn_list:
            forecast[row_name] = []
            row = soup.find("tr", {"data-row-name": row_name})
            cells = row.find_all("td")
            for cell in cells:
                if cell.text.strip() != "":
                    forecast[row_name].append(cell.text)
        forecast = rename_key(forecast, "wind-state", "wind_status")
        forecast = rename_key(forecast, "wave-height", "wave_height")
        forecast = rename_key(forecast, "periods", "wave_period")
        forecast = self.add_days_to_forecast(forecast)
        forecast["spot_name"] = self.parse_spot_names(spot_name, len(forecast["date"]))
        forecast["wind_status"] = self.get_formatted_wind_status(forecast)
        forecast["wave_height"] = self.get_formatted_wave_height(forecast)
        return pd.DataFrame(forecast)

    def conditions(self, df: pd.DataFrame) -> pd.DataFrame:
        wave_height = df["wave_height"].astype(float)

        period = df["wave_period"].astype(float)

        # STRENGTH
        STRENGTH = wave_height >= 1  # & (primary_wave_heigh <= 2.5)

        # PERIOD
        PERIOD = period >= 6

        WIND_STATUS = (df["wind_status"] == "Offshore") | (
            df["wind_status"] == "Cross-off"
        )

        favorable = STRENGTH & PERIOD & WIND_STATUS

        default = "No Favorable"

        str_list = ["Favorable"]

        df["approval"] = np.select(
            [favorable],
            str_list,
            default=default,
        )
        return df

    def format_dataframe(self, df):
        # Hacerlo en menos lineas comprobando que la hora es de noche
        df = df.drop(
            df[
                (df["time"] == "03h")
                | (df["time"] == "04h")
                | (df["time"] == "05h")
                | (df["time"] == "21h")
            ].index
        )
        return df

    def process_soup(self, soup):
        df = self.get_dataframe_from_soup(soup)
        df = self.conditions(df)
        return self.format_dataframe(df)

    def scrape(self, url):
        response = self.beach_request(url)
        soup = BeautifulSoup(response.text, "html.parser")
        return self.process_soup(soup)
