from bs4 import BeautifulSoup
from typing import Dict
import polars as pl
from utils import (
    rename_key,
    generate_tides,
    generate_nearest_tides,
    generate_tide_percentages,
    generate_energy,
    render_html,
    generate_datetimes,
    filter_spot_dataframe,
)
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
from APIS.discord_api import DiscordBot


class Windguru(object):
    def __init__(self):
        pass

    def beach_request(self, url):
        r_text = render_html(url=url, tag_to_wait="table.tabulka", timeout=60 * 1000)
        return BeautifulSoup(r_text, "html.parser")

    def format_forecast(self, forecast: Dict, tides: dict) -> Dict:
        forecast = rename_key(forecast, "tabid_0_0_dates", "datetime")
        forecast = rename_key(forecast, "tabid_0_0_SMER", "wind_direction_raw")
        forecast = rename_key(forecast, "tabid_0_0_HTSGW", "wave_height")
        forecast = rename_key(forecast, "tabid_0_0_DIRPW", "wave_direction_raw")
        forecast = rename_key(forecast, "tabid_0_0_PERPW", "wave_period")
        forecast = rename_key(forecast, "tabid_0_0_WINDSPD", "wind_speed")
        forecast = rename_key(forecast, "tabid_0_0_TMPE", "temperature")

        forecast["wind_direction"] = [
            self.parse_text_from_text(element)
            for element in forecast["wind_direction_raw"]
        ]
        forecast["wave_direction"] = [
            self.parse_text_from_text(element)
            for element in forecast["wave_direction_raw"]
        ]
        forecast["wind_direction_degrees"] = [
            self.parse_number_from_text(element)
            for element in forecast["wind_direction_raw"]
        ]
        forecast["wave_direction_degrees"] = [
            self.parse_number_from_text(element)
            for element in forecast["wave_direction_raw"]
        ]

        forecast["date"] = [
            self.datestr_to_backslashformat(dt.split(".")[0])
            for dt in forecast["datetime"]
        ]
        forecast["time"] = [
            dt.split(".")[1].replace("h", ":00") for dt in forecast["datetime"]
        ]
        forecast["datetime"] = generate_datetimes(forecast["date"], forecast["time"])

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
        forecast["tide"] = generate_tides(tides, forecast["datetime"])
        forecast["nearest_tide"] = generate_nearest_tides(tides, forecast["datetime"])
        forecast["tide_percentage"] = generate_tide_percentages(
            tides, forecast["datetime"]
        )
        forecast["energy"] = generate_energy(
            forecast["wave_height"], forecast["wave_period"]
        )
        return forecast

    def parse_spot_name(self, soup):
        return soup.select("div.spot-name.wg-guide")[0].text.strip()

    def parse_spot_names(self, soup, total_records):
        return [self.parse_spot_name(soup) for _ in range(total_records)]

    def get_dataframe_from_soup(self, soup: BeautifulSoup, tides: dict) -> Dict:
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
                "tabid_0_0_TMPE",
            ]:
                forecast[id] = []
                for cell in cells:
                    if ("SMER" in id) | ("DIRPW" in id):
                        try:
                            value = cell.select("span")[0]["title"]
                        except Exception as e:
                            value = "NAN (-69°)"
                    else:
                        value = cell.get_text().replace("-", "-69")
                    forecast[id].append(value)
        if forecast != {}:
            total_records = len(max(forecast.items(), key=lambda item: len(item[1]))[1])
            forecast["spot_name"] = self.parse_spot_names(soup, total_records)
            forecast = self.format_forecast(forecast, tides)
            return pl.DataFrame(forecast)
        return pl.DataFrame()

    # def parse_number_from_text(self, text):
    #     pattern = r"(\d+)°"

    #     match = re.search(pattern, text)
    #     if match:
    #         return int(match.group(1))
    #     return None

    def parse_text_from_text(self, text):
        return text.split(" ")[0]

    def parse_number_from_text(self, text):
        pattern = r"(\d+)°"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1))

    def parse_windstatus(self, wave_directions, wind_directions):
        # TODO crear esta columna sin cálculos, de cabeza
        return [
            # get_wind_status(wind_dir, wave_dir)
            "Offshore"
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
        if int(month) < current_date.month:
            new_date = current_date + relativedelta(years=1)
            year = new_date.year
        elif int(month) >= current_date.month:
            year = current_date.year
        date_datetime = datetime.strptime(f"{day}/{month}/{year}", "%d/%m/%Y")

        return date_datetime.strftime("%d/%m/%Y")

    def handle_windguru_alerts(self, df: pl.DataFrame):
        famara_df = filter_spot_dataframe("famara", df, three_near_days=True)
        tiburon_df = filter_spot_dataframe("tiburon", df, three_near_days=True)
        barcarola_df = filter_spot_dataframe("barcarola", df, three_near_days=True)
        bastian_df = filter_spot_dataframe("bastian", df, three_near_days=True)
        punta_df = filter_spot_dataframe("punta_mujeres", df, three_near_days=True)
        arrieta_df = filter_spot_dataframe("arrieta", df, three_near_days=True)
        spots_df = [
            # caleta_caballo_df,
            tiburon_df,
            barcarola_df,
            bastian_df,
            punta_df,
            arrieta_df,
            famara_df,
        ]
        for df in spots_df:
            if not df.is_empty():
                # result_df = df.filter(df)
                discort_bot = DiscordBot()
                for row in df.rows(named=True):
                    discort_bot.waves_alert(
                        f"windguru - **{row['spot_name'].upper()}**: {row['date_name']}, día {row['date']} a las {row['time']}, una altura de {row['wave_height']}, un periodo de {row['wave_period']} y una direccion del viento de {row['wind_direction']} y una direccion de la ola de {row['wave_direction']}, velocidad del viento de {row['wind_speed']} y la marea estará {row['tide']}"
                    )
        return

    def scrape(self, arguments: tuple):
        url, tides = arguments
        soup = self.beach_request(url)
        return self.get_dataframe_from_soup(soup, tides)
