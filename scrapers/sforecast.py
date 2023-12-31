from bs4 import BeautifulSoup
import requests
import polars as pl
from utils import (
    rename_key,
    kmh_to_knots,
    generate_dates,
    generate_tides,
    generate_datetimes,
)
from datetime import datetime, timedelta
import re
from dateutil import parser
from APIS.discord_api import DiscordBot


class SurfForecast(object):
    def __init__(self):
        self.headers = {
            "authority": "www.surf-forecast.com",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "es-ES,es;q=0.9",
            "Accept-Language": "es-ES,es;q=0.9",
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

    def parse_spot_name(self, soup):
        return soup.find_all("option", selected=True)[3].text

    def parse_spot_names(self, spot_name, total_records):
        return [spot_name for _ in range(total_records)]

    def get_formated_energy(self, forecast):
        energy = list(forecast["energy"])
        return [int(element) for element in energy]

    def get_formatted_wind_status(self, forecast):
        new_wind_status = []
        translator = {
            "on": "Onshore",
            "off": "Offshore",
            "cross": "Crossshore",
            "cross-off": "Cross-off",
            "cross-on": "Cross-on",
            "glass": "Glass",
        }
        for element in forecast["wind_status"]:
            if element in translator:
                new_wind_status.append(translator[element])
            else:
                raise Exception(f"Element {element} not in translator")
        return new_wind_status

    def get_formatted_wave_height(self, forecast):
        wave_height_list = []
        pattern = r"(\d+(\.\d+)?)"
        for element in forecast["wave"]:
            match = re.match(pattern, element)
            if match:
                wave_height = float(match.group(1))
                wave_height_list.append(wave_height)
        return wave_height_list

    def get_formatted_wave_direction(self, forecast):
        wave_direction_list = []
        pattern = r"(\d+(\.\d+)?)"
        for element in forecast["wave"]:
            match = re.match(pattern, element)
            if match:
                numeric_value = str(match.group(1))
                char_value = element.split(numeric_value)[1]
                wave_direction_list.append(char_value.strip())
        return wave_direction_list

    def obtain_formated_wave_period(self, forecast):
        return [
            int(forecast["wave_period"][i]) for i in range(len(forecast["wave_period"]))
        ]

    def get_formatted_wind_direction(self, forecast):
        wind_direction_list = []
        pattern = r"(\d+(\.\d+)?)"
        for element in forecast["wind"]:
            match = re.match(pattern, element)
            if match:
                wind_direction_degrees = str(match.group(1))
                char_value = element.split(wind_direction_degrees)[1]
                wind_direction_list.append(char_value.strip())
        return wind_direction_list

    def get_formatted_wind_speed(self, forecast):
        wind_direction_list = []
        pattern = r"(\d+(\.\d+)?)"
        for element in forecast["wind"]:
            match = re.match(pattern, element)
            if match:
                wind_speed = float(match.group(1))
                wind_direction_list.append(kmh_to_knots(wind_speed))
        return wind_direction_list

    def convert_to_Hm(self, time_str):
        return parser.parse(time_str).strftime("%H:%M")

    def obtain_formated_time(self, forecast):
        time_list = []
        for time in forecast["time"]:
            if "\u2009" in time:
                extracted_time = self.convert_to_Hm(time.replace("\u2009", ""))
            elif time in ["mañana", "tarde", "noche"]:
                extracted_time = (
                    time.replace("mañana", "09:00")
                    .replace("tarde", "15:00")
                    .replace("noche", "21:00")
                )
            elif time in ["AM", "PM", "Night"]:
                extracted_time = (
                    time.replace("AM", "09:00")
                    .replace("PM", "15:00")
                    .replace("Night", "21:00")
                )
            time_list.append(extracted_time)
        return time_list

    def get_dataframe_from_soup(self, soup, tides):
        forecast = {}
        spot_name = self.parse_spot_name(soup)
        drn_list = [
            "time",
            "wave-height",
            "periods",
            "energy",
            "wind",
            "wind-state",
            "energy",
        ]
        for row_name in drn_list:
            forecast[row_name] = []
            row = soup.find("tr", {"data-row-name": row_name})
            cells = row.find_all("td")
            for cell in cells:
                if cell.text.strip() != "":
                    forecast[row_name].append(cell.text)
        forecast = rename_key(forecast, "wind-state", "wind_status")
        forecast = rename_key(forecast, "wave-height", "wave")
        forecast = rename_key(forecast, "periods", "wave_period")
        forecast["wind_status"] = self.get_formatted_wind_status(forecast)
        forecast["wave_height"] = self.get_formatted_wave_height(forecast)
        forecast["wave_direction"] = self.get_formatted_wave_direction(forecast)
        del forecast["wave"]
        forecast["wind_direction"] = self.get_formatted_wind_direction(forecast)
        forecast["wind_speed"] = self.get_formatted_wind_speed(forecast)
        forecast["wave_period"] = self.obtain_formated_wave_period(forecast)
        times = self.obtain_formated_time(forecast)
        dates = generate_dates(times)
        datetimes = generate_datetimes(dates, times)
        forecast["time"] = times
        forecast["date"] = dates
        forecast["datetime"] = datetimes
        forecast["spot_name"] = self.parse_spot_names(spot_name, len(forecast["time"]))
        forecast["energy"] = self.get_formated_energy(forecast)
        forecast["tide"] = generate_tides(tides, datetimes)
        # forecast = convert_all_values_of_dict_to_min_length(forecast)
        df = pl.DataFrame(forecast)
        # df = self.remove_night_times(df)
        return df

    def handle_sforecast_alerts(self, df: pl.DataFrame):
        DATE_NAME_IN_LIST = df["date_name"].is_in(["Hoy", "Mañana", "Pasado"])
        WIND_STATUS_IN_LIST = df["wind_status"].is_in(
            ["Offshore", "Cross-off", "Glass"]
        )
        papagayo_conditions = (
            df["spot_name"].str.contains("Playa de la Cera")
            & (df["energy"] >= 1500)
            & ((df["wave_direction"] == "WNW") | (df["wave_direction"] == "W"))
            & (DATE_NAME_IN_LIST)
        )
        caleta_caballo_conditions = (
            (
                (df["wind_direction"].str == "W")
                or (df["wind_direction"].str.contains("SW"))
            )
            & (df["spot_name"].str.contains("Caleta de Cabello"))
            & (DATE_NAME_IN_LIST)
            & (WIND_STATUS_IN_LIST)
        )
        famara_conditions = (
            (df["wind_direction"].str.contains("S"))
            & (df["spot_name"].str.contains("Famara"))
            & (df["energy"] >= 100)
            & (DATE_NAME_IN_LIST)
            & (WIND_STATUS_IN_LIST)
        )
        tiburon_conditions = (
            df["spot_name"].str.contains("Tiburon")
            & (df["energy"] >= 1000)
            & (DATE_NAME_IN_LIST)
            & (WIND_STATUS_IN_LIST)
        )
        barcarola_conditions = (
            df["spot_name"].str.contains("Barcarola")
            & (df["energy"] >= 1000)
            & (DATE_NAME_IN_LIST)
            & (WIND_STATUS_IN_LIST)
        )

        bastian_conditions = (
            df["spot_name"].str.contains("Bastián")
            & (df["energy"] >= 1000)
            & (DATE_NAME_IN_LIST)
            & (WIND_STATUS_IN_LIST)
        )
        punta_conditions = (
            df["spot_name"].str.contains("Punta de Mujeres")
            & (df["wind_direction"].str.contains("N"))
            & (df["wave_direction"].str.contains("E"))
            & (df["energy"] >= 1000)
            & (DATE_NAME_IN_LIST)
        )
        arrieta_conditions = (
            df["spot_name"].str.contains("Arrieta")
            & (df["wind_direction"].str.contains("N"))
            & (df["wave_direction"].str.contains("E"))
            & (df["energy"] >= 1000)
            & (DATE_NAME_IN_LIST)
        )
        spots_conditions = [
            papagayo_conditions,
            caleta_caballo_conditions,
            tiburon_conditions,
            barcarola_conditions,
            bastian_conditions,
            punta_conditions,
            arrieta_conditions,
            famara_conditions,
        ]
        for condition in spots_conditions:
            if condition.any():
                result_df = df.filter(condition)
                discort_bot = DiscordBot()
                for row in result_df.rows(named=True):
                    discort_bot.waves_alert(
                        f"surf-forecast - **{row['spot_name'].upper()}**: {row['date_name']}, día {row['date']} a las {row['time']} con una energía de {row['energy']}, una direccion del viento de {row['wind_direction']} y una direccion de la ola de {row['wave_direction']} y la marea estará {row['tide']}"
                    )
        return

    def remove_night_times(self, df):
        return df.filter(pl.col("time") != "Night")

    def scrape(self, url, tides):
        response = self.beach_request(url)
        soup = BeautifulSoup(response.text, "html.parser")
        df = self.get_dataframe_from_soup(soup, tides)
        return df
