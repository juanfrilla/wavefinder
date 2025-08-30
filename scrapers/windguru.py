from datetime import datetime, timezone
import polars as pl
from utils import (
    generate_tides,
    generate_nearest_tides,
    generate_tide_percentages,
    generate_energy,
    create_date_name_column,
    create_direction_predominant_column,
    generate_spot_names,
    datetime_to_frontend_str,
    degrees_to_direction,
    generate_forecast_moments,
    ammend_wave_directions,
    clean_list,
    align_dict_columns,
)
import locale
import requests
import math

locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")


class Windguru(object):
    def __init__(self):
        pass

    def generate_rundef(
        self,
        forecast_start=0,
        forecast_end=240,
        long_range_start=243,
        long_range_end=384,
    ):
        now_dt = datetime.now(timezone.utc)

        if now_dt.hour >= 12:
            model_run_time = now_dt.replace(hour=12, minute=0, second=0, microsecond=0)
        else:
            model_run_time = now_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        init_time_str = model_run_time.strftime("%Y%m%d%H")
        rundef = f"{init_time_str}x{forecast_start}x{forecast_end}x{forecast_start}x{forecast_end}-{init_time_str}x{long_range_start}x{long_range_end}x{long_range_start}x{long_range_end}"

        return rundef

    def get_wind_from_api(self, id_spot: str):
        rundef = self.generate_rundef()
        headers = {
            "sec-ch-ua-platform": '"Windows"',
            "Referer": "https://www.windguru.cz/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
        }

        params = {
            "q": "forecast",
            "id_model": "3",
            "rundef": rundef,
            "id_spot": id_spot,
            "WGCACHEABLE": "21600",
            "cachefix": "29.123x-13.542x-1",
        }

        return requests.get(
            "https://www.windguru.net/int/iapi.php", params=params, headers=headers
        )

    def get_waves_from_api(self, id_spot: str):
        rundef = self.generate_rundef()
        headers = {
            "sec-ch-ua-platform": '"Windows"',
            "Referer": "https://www.windguru.cz/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
        }

        params = {
            "q": "forecast",
            "id_model": "84",
            "rundef": rundef,
            "id_spot": id_spot,
            "WGCACHEABLE": "21600",
            "cachefix": "29.209x-13.676x-1",
        }

        return requests.get(
            "https://www.windguru.net/int/iapi.php", params=params, headers=headers
        )

    def scrape_with_request(self, waves_data: dict, wind_data: dict, tides: dict):
        forecast = {}
        wind_speed = clean_list(wind_data.get("fcst").get("WINDSPD"))
        wind_direction_degrees = clean_list(wind_data.get("fcst").get("WINDDIR"))
        wave_height = clean_list(waves_data.get("fcst").get("HTSGW"))
        wave_direction_degrees = clean_list(waves_data.get("fcst").get("DIRPW"))
        wave_period = clean_list(waves_data.get("fcst").get("PERPW"))
        initstamp = int(wind_data.get("fcst").get("initstamp"))
        hours = wind_data.get("fcst").get("hours")

        moments = generate_forecast_moments(initstamp, hours)

        forecast["wind_speed"] = [math.ceil(element) for element in wind_speed]
        forecast["wind_direction_degrees"] = wind_direction_degrees
        forecast["wave_height"] = [math.ceil(element) for element in wave_height]
        forecast["wave_direction_degrees"] = wave_direction_degrees
        forecast["wave_period"] = [math.ceil(element) for element in wave_period]
        forecast["datetime"] = moments
        forecast["date"] = [moment.date() for moment in moments]
        forecast["date_friendly"] = [
            datetime_to_frontend_str(moment) for moment in moments
        ]
        forecast["time"] = [moment.time() for moment in moments]
        time_friendly = [moment.strftime("%H:%M") for moment in moments]
        forecast["time_friendly"] = time_friendly
        forecast["time_graph"] = [
            element.replace(":", r"\:") for element in time_friendly
        ]

        forecast["wind_direction_predominant"] = create_direction_predominant_column(
            wind_direction_degrees
        )
        forecast["wind_direction"] = [
            degrees_to_direction(element) for element in wind_direction_degrees
        ]
        forecast["wave_direction_predominant"] = create_direction_predominant_column(
            wave_direction_degrees
        )
        wave_directions = [
            degrees_to_direction(element) for element in wave_direction_degrees
        ]
        forecast["wave_direction"] = ammend_wave_directions(
            wave_directions, wave_direction_degrees
        )
        forecast["energy"] = generate_energy(wave_height, wave_period)

        forecast["tide"] = generate_tides(tides, forecast["datetime"])
        forecast["nearest_tide"] = generate_nearest_tides(tides, forecast["datetime"])
        forecast["tide_percentage"] = generate_tide_percentages(
            tides, forecast["datetime"]
        )
        forecast["spot_name"] = generate_spot_names(forecast)
        forecast["date_name"] = create_date_name_column(forecast["datetime"])

        format_forecast = align_dict_columns(forecast)
        return pl.DataFrame(format_forecast)
