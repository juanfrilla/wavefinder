import requests
from bs4 import BeautifulSoup, Tag
import pandas as pd
from utils import (
    import_html,
    get_wind_status,
    angle_to_direction,
    convert_datestr_format,
    convert_all_values_of_dict_to_min_length,
)
import json
import re
import ast
from datetime import datetime


# import chompjs


class WindFinder(object):
    def __init__(self):
        self.headers = {
            "authority": "es.windfinder.com",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "es-ES,es;q=0.9",
            "cache-control": "max-age=0",
            "sec-ch-ua": '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "cross-site",
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

    def format_direction_arrow(self, direction_arrow: str):
        title = direction_arrow["title"]
        format_title = title.replace("°", "")
        return angle_to_direction(float(format_title))

    def format_period_height(self, soup):
        next_element = soup.next
        return int(self.text_strip(next_element))

    def text_strip(self, div: Tag):
        return div.text.strip()

    def parse_spot_name(self, soup):
        return soup.select("span#spotheader-spotname")[0].text.strip()

    def parse_wave_directions(self, fetched_list):
        return [angle_to_direction(int(element["wad"])) for element in fetched_list]

    def parse_wind_directions(self, fetched_list):
        return [angle_to_direction(int(element["wd"])) for element in fetched_list]

    def parse_hour_intervals(self, soup):
        hour_intervals_table = soup.select(
            "div.cell-timespan.weathertable__cellgroup.weathertable__cellgroup--stacked"
        )
        return [
            self.text_strip(hour_interval_table).replace("h", ":00")
            for hour_interval_table in hour_intervals_table
        ]

    def parse_wave_periods(self, soup):
        wave_periods_table = soup.select(
            "div.data-wavefreq.data--minor.weathertable__cell"
        )
        return [
            self.format_period_height(wave_period_table)
            for wave_period_table in wave_periods_table
        ]

    def parse_wave_heights(self, fetched_list):
        return [float(element["wh"]) for element in fetched_list]

    def parse_wind_speeds(self, fetched_list):
        return [float(element["ws"]) for element in fetched_list]

    def date_str_to_datetime(self, date_string):
        return datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S%z")

    def parse_datetimes(self, fetched_list):
        return [self.date_str_to_datetime((element["dtl"])) for element in fetched_list]

    def parse_spot_names(self, spot_name, total_records):
        return [spot_name for _ in range(total_records)]

    def parse_dates_str(self, soup, total_records):
        wearthable_headers = soup.select("div.weathertable__header > h3")
        dates_str = [
            convert_datestr_format(self.text_strip(date_str))
            for date_str in wearthable_headers
        ]
        total_dates = len(dates_str)
        return [
            element
            for element in dates_str
            for _ in range(int(total_records / total_dates))
        ]

    def parse_windstatus(self, wave_directions, wind_directions):
        return [
            get_wind_status(wind_dir, wave_dir)
            for wave_dir, wind_dir in zip(wave_directions, wind_directions)
        ]

    def sample_soup(self, filename):
        html_content = import_html(filename)
        return BeautifulSoup(html_content, "html.parser")

    def obtain_data(self, soup: BeautifulSoup):
        script_tags = soup.select("script")
        for script in script_tags:
            script_text = script.text
            if "window.ctx.push" in script_text and "fcdata" in script_text.lower():
                splitted = script_text.split("window.ctx.push(")
                for splittext in splitted:
                    without_push_splitted = (
                        splittext.replace("window.ctx.push(", "")
                        .replace(");", "")
                        .split("fcData:")
                    )
                    if len(without_push_splitted) > 1:
                        without_push_text = (
                            without_push_splitted[1].split("]")[0].strip() + "]"
                        ).replace(": null", ": 0")
                        fetched_list = ast.literal_eval(without_push_text)

        wave_directions = self.parse_wave_directions(fetched_list)
        wind_directions = self.parse_wind_directions(fetched_list)
        wave_heights = self.parse_wave_heights(fetched_list)
        wind_speeds = self.parse_wind_speeds(fetched_list)
        datetimes = self.parse_datetimes(fetched_list)
        wind_statuses = self.parse_windstatus(wave_directions, wind_directions)
        wave_periods = self.parse_wave_periods(soup)
        total_records = len(datetimes)
        spot_names = self.parse_spot_names(self.parse_spot_name(soup), total_records)

        data = {
            "datetime": datetimes,
            "wave_direction": wave_directions,
            "wind_direction": wind_directions,
            "wind_status": wind_statuses,
            "wave_period": wave_periods,
            "wave_height": wave_heights,
            "wind_speed": wind_speeds,
            "spot_name": spot_names,
        }
        data = convert_all_values_of_dict_to_min_length(data)
        return data

    def get_dataframe_from_soup(self, soup):
        data = self.obtain_data(soup)
        return pd.DataFrame(data)

    def scrape(self, url):
        response = self.beach_request(url)
        soup = BeautifulSoup(response.text, "html.parser")
        return self.get_dataframe_from_soup(soup)
