from bs4 import BeautifulSoup
import requests
import polars as pl
from utils import (
    rename_key,
    kmh_to_knots,
    convert_all_values_of_dict_to_min_length,
    generate_dates,
)
from datetime import datetime, timedelta
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
        # Preprocess the string to replace '0' with '12' if needed
        if time_str.startswith("0"):
            time_str = "12" + time_str[1:]

        # Use %I for hours and %p for AM/PM
        datetime_object = datetime.strptime(time_str, "%I%p")

        # Format the result as 'H:m'
        return datetime_object.strftime("%H:%M")

    def obtain_formated_time(self, forecast):
        time_list = []
        for time in forecast["time"]:
            time.replace("\u2009", "")
            # if time in ["AM", "PM", "Night"]:
            # time = (
            #     time.replace("AM", "10:00")
            #     .replace("PM", "16:00")
            #     .replace("Night", "22:00")
            # )
            extracted_time = time.replace("\u2009", "")
            time_list.append(self.convert_to_Hm(extracted_time))
        return time_list

    def generate_datetimes(self, dates, times):
        datetimes = []
        for date, time in zip(dates, times):
            year = datetime.strptime(date, "%d/%m/%Y").year
            month = datetime.strptime(date, "%d/%m/%Y").month
            day = datetime.strptime(date, "%d/%m/%Y").day
            hour = int(time.split(":")[0])
            minute = int(time.split(":")[1])
            datetimes.append(datetime(year, month, day, hour, minute))
        return datetimes

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
        forecast["datetime"] = self.generate_datetimes(dates, times)
        forecast["spot_name"] = self.parse_spot_names(spot_name, len(forecast["time"]))
        forecast["energy"] = self.get_formated_energy(forecast)
        # forecast = convert_all_values_of_dict_to_min_length(forecast)
        df = pl.DataFrame(forecast)
        # df = self.remove_night_times(df)
        return df

    def remove_night_times(self, df):
        return df.filter(pl.col("time") != "Night")

    def scrape(self, url):
        response = self.beach_request(url)
        soup = BeautifulSoup(response.text, "html.parser")
        try:
            df = self.get_dataframe_from_soup(soup)
        except Exception as e:
            raise ValueError(f"Error scraping {url}: {e}")
        return df
