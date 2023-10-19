from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
from utils import (
    angle_to_direction,
    get_wind_status,
    render_html,
    convert_all_values_of_dict_to_min_length,
    mps_to_knots,
    generate_dates,
)
import re


class WindyApp(object):
    def __init__(self):
        pass

    def beach_request(self, url, timeout=10):
        r_text = render_html(url=url, tag_to_wait="tr.windywidgetdays", timeout=timeout)
        return BeautifulSoup(r_text, "html.parser")

    def parse_formated_time(self, soup: BeautifulSoup) -> list:
        raw_time = soup.select("tr.windywidgethours > td")[1:]
        base_time = datetime(2023, 1, 1, 0, 0)
        return [(base_time + timedelta(hours=int(time.text))).time().strftime("%H:%M") for time in raw_time]
    
    def generate_datetimes(self, dates, times):
        return [
            datetime.strptime(f"{date} {time}", "%d/%m/%Y %H:%M")
            for date, time in zip(dates, times)
        ]

    def parse_number_from_style(self, style: str) -> int:
        regex = r"rotate\((\d+)deg\)"
        match = re.search(regex, style)
        return int(match.group(1))

    def convert_angle_between_0_and_360(self, angle: int):
        if angle > 360:
            angle = angle - 360
        return angle

    def parse_formated_wind_direction(self, soup: BeautifulSoup) -> list:
        raw_wind_direction = soup.select(
            "tr.windywidgetwindDirection.id-wind-direction > td"
        )[1:]
        return self.angles_to_text(raw_wind_direction)

    def parse_formated_wind_speed(self, soup: BeautifulSoup) -> list:
        raw_wind_speed = soup.select("tr.windywidgetwindSpeed.id-wind-speed > td")[1:]
        return [mps_to_knots(float(speed.text)) for speed in raw_wind_speed]

    def angles_to_text(self, angles: list) -> list:
        raw_styles = [style["style"] for style in angles]

        unformated_wind_direction = []
        for style in raw_styles:
            angle = self.parse_number_from_style(style) + 180
            unformated_wind_direction.append(angle)
        converted_angles = [
            self.convert_angle_between_0_and_360(angle)
            for angle in unformated_wind_direction
        ]
        return [angle_to_direction(angle) for angle in converted_angles]

    def parse_formated_waves_direction(self, soup: BeautifulSoup) -> list:
        raw_waves_direction = soup.select(
            "tr.windywidgetwaves.id-waves-direction > td > div"
        )[1:]
        return self.angles_to_text(raw_waves_direction)

    def parse_formated_waves_height(self, soup: BeautifulSoup) -> list:
        raw_waves_height = soup.select(
            "tr.windywidgetwavesheight.id-waves-height > td"
        )[1:]
        return [float(heigth.text) for heigth in raw_waves_height]

    def parse_formated_waves_period(self, soup: BeautifulSoup) -> list:
        raw_waves_period = soup.select(
            "tr.windywidgetwavesperiod.id-waves-period > td"
        )[1:]
        parsed_periods = []
        for period in raw_waves_period:
            stripped_text = period.text.strip("'")
            if stripped_text.isdigit():
                parsed_periods.append(int(stripped_text))
            else:
                break
        return parsed_periods

    def parse_windstatus(self, wave_directions, wind_directions):
        return [
            get_wind_status(wind_dir, wave_dir)
            for wave_dir, wind_dir in zip(wave_directions, wind_directions)
        ]

    def parse_spot_name(self, soup):
        return soup.select("a#windywidgetspotname")[0].text

    def parse_spot_names(self, spot_name, total_records):
        return [spot_name for _ in range(total_records)]

    def get_dataframe_from_soup(self, soup):
        data = self.obtain_data(soup)
        return pd.DataFrame(data)

    def format_dataframe(self, df):
        df = df.drop(
            df[
                (df["time"] == 22)
                | (df["time"] == 1)
                | (df["time"] == 4)
                | (df["time"] == 0)
            ].index
        )
        return df

    def obtain_data(self, soup):
        wind_directions = self.parse_formated_wind_direction(soup)
        wind_speeds = self.parse_formated_wind_speed(soup)
        wave_directions = self.parse_formated_waves_direction(soup)
        waves_heigths = self.parse_formated_waves_height(soup)
        waves_periods = self.parse_formated_waves_period(
            soup
        )  # este marca el tamaño de la lista
        times = self.parse_formated_time(soup)
        dates = generate_dates(times)
        datetimes = self.generate_datetimes(dates, times)
        data = {
            "datetime": datetimes,
            "wave_direction": wave_directions,
            "wind_direction": wind_directions,
            "wind_status": self.parse_windstatus(wave_directions, wind_directions),
            "wave_period": waves_periods,
            "wave_height": waves_heigths,
            "wind_speed": wind_speeds,
        }
        total_records = len(data["datetime"])
        data["spot_name"] = self.parse_spot_names(
            self.parse_spot_name(soup), total_records
        )
        data = convert_all_values_of_dict_to_min_length(data)
        return data

    def parse_widget_wrapper(self, soup: BeautifulSoup):
        return soup.select(
            "div.row > div.col-12.col-md-12.col-widget.px-0.px-sm-3.forecast-widget-wrapper"
        )[0]

    def scrape(self, url):
        soup = self.beach_request(url, 60)
        return self.get_dataframe_from_soup(soup)
