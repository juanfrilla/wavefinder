from bs4 import BeautifulSoup
from typing import Dict
import polars as pl
from utils import (
    rename_key,
    angle_to_direction,
    get_wind_status,
    render_html,
    import_html,
    timestamp_to_datetime,
    feet_to_meters,
)
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
from urllib.parse import urlparse, parse_qs


class WindyCom(object):
    def beach_request(self, url):
        r_text = render_html(
            url=url,
            tag_to_wait="tr.td-waves.height-waves.d-display-waves",
            # tag_to_wait="div#desktop-premium-icon",
            timeout=60 * 1000,
        )

        return BeautifulSoup(r_text, "html.parser")

    def get_wind_speeds(self, table: BeautifulSoup):
        winds = table.select(
            "tbody > tr.td-windCombined.height-windCombined.d-display-waves > td"
        )
        smalls = table.select(
            "tbody > tr.td-windCombined.height-windCombined.d-display-waves > td > small"
        )
        new_winds = []
        for small, wind in zip(smalls, winds):
            small_text = small.text.strip()
            wind_text = wind.text.strip()
            wind_text = wind_text[1:]
            small_len = len(small_text)
            wind = wind_text[:small_len]
            new_winds.append(int(wind))
        return new_winds

    def get_wind_directions(self, table: BeautifulSoup):
        winds = table.select(
            "tbody > tr.td-windCombined.height-windCombined.d-display-waves > td > div"
        )

        return self.angles_to_text(winds)

    def get_wave_periods(self, table):
        periods = table.select(
            "tbody > tr.td-swell1Period.height-swell1Period.d-display-waves > td"
        )
        periods = [float(period.text) for period in periods]
        return periods

    def get_wave_heights(self, table):
        wave_heights = table.select(
            "tbody > tr.td-waves.height-waves.d-display-waves > td"
        )
        wave_heights = [
            feet_to_meters(float(height.text[1:])) for height in wave_heights
        ]

        return wave_heights

    def get_wave_directions(self, table):
        wave_directions = table.select(
            "tbody > tr.td-waves.height-waves.d-display-waves > td > div"
        )
        return self.angles_to_text(wave_directions)

    def angles_to_text(self, angles: list) -> list:
        raw_styles = [style["style"] for style in angles]

        unformated_wind_direction = []
        for style in raw_styles:
            angle = self.parse_number_from_style(style)
            unformated_wind_direction.append(angle)
        converted_angles = [
            self.convert_angle_between_0_and_360(angle)
            for angle in unformated_wind_direction
        ]
        return [angle_to_direction(angle) for angle in converted_angles]

    def convert_angle_between_0_and_360(self, angle: int):
        if angle > 360:
            angle = angle - 360
        return angle

    def parse_number_from_style(self, style: str) -> int:
        regex = r"rotate\((\d+)deg\)"
        match = re.search(regex, style)
        return int(match.group(1))

    def get_datetimes(self, table):
        datetimes = []
        tds = table.select("tbody > tr.td-hour.height-hour.d-display-waves > td")
        for td in tds:
            timestamp = int(td["data-ts"]) / 1000
            dt = timestamp_to_datetime(timestamp)
            datetimes.append(dt)
        return datetimes

    def parse_windstatus(self, wave_directions, wind_directions):
        return [
            get_wind_status(wind_dir, wave_dir)
            for wave_dir, wind_dir in zip(wave_directions, wind_directions)
        ]

    def parse_spot_name(self, url):
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        return list(query_params.values())[0][0].replace("_", " ")

    def repeat_field_n_times(self, field, n):
        return [field] * n

    def scrape(self, url):
        forecast = {}
        soup = self.beach_request(url)
        # text = import_html("samples/table_windycom.html")
        # soup = BeautifulSoup(text, "html.parser")
        table = soup.select("table")[0]
        forecast["wind_speed"] = self.get_wind_speeds(table)
        forecast["wind_direction"] = self.get_wind_directions(table)
        forecast["wave_period"] = self.get_wave_periods(table)
        forecast["wave_height"] = self.get_wave_heights(table)
        forecast["wave_direction"] = self.get_wave_directions(table)
        forecast["wind_status"] = self.parse_windstatus(
            forecast["wave_direction"], forecast["wind_direction"]
        )
        forecast["datetime"] = self.get_datetimes(table)
        forecast["spot_name"] = self.repeat_field_n_times(
            self.parse_spot_name(url), len(forecast["datetime"])
        )
        return pl.DataFrame(forecast)

        # return self.get_dataframe_from_soup(soup)
