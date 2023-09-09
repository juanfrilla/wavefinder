import requests
from bs4 import BeautifulSoup, Tag
import pandas as pd
from utils import (
    import_html,
    get_wind_status,
    angle_to_direction,
    convert_datestr_format
)


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

    def parse_wave_directions(self, soup):
        wave_direction_arrows = soup.select(
            "div.directionarrow.icon-direction-stroke-grey"
        )
        return [
            self.format_direction_arrow(wave_direction_arrow)
            for wave_direction_arrow in wave_direction_arrows
        ]

    def parse_wind_directions(self, soup):
        wind_direction_arrows = soup.select(
            "div.directionarrow.icon-direction-solid-grey"
        )
        return [
            self.format_direction_arrow(wind_direction_arrow)
            for wind_direction_arrow in wind_direction_arrows
        ]

    def parse_hour_intervals(self, soup):
        hour_intervals_table = soup.select(
            "div.cell-timespan.weathertable__cellgroup.weathertable__cellgroup--stacked"
        )
        return [
            self.text_strip(hour_interval_table)
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

    def parse_wave_heights(self, soup):
        wave_heights_table = soup.select(
            "div.data-waveheight.data--major.weathertable__cell > span.units-wh"
        )
        return [
            float(self.text_strip(wave_height_table))
            for wave_height_table in wave_heights_table
        ]

    def parse_wind_speeds(self, soup):
        wind_speeds_table = soup.select("div.speed > span.data-wrap > span.units-ws")
        return [float(self.text_strip(wind_speed)) for wind_speed in wind_speeds_table]

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

    def format_dataframe(self, df):
        df = df.drop(
            df[
                (df["time"] == "01h") | (df["time"] == "04h") | (df["time"] == "22h")
            ].index
        )
        return df

    def sample_soup(self, filename):
        html_content = import_html(filename)
        return BeautifulSoup(html_content, "html.parser")

    def get_dataframe_from_soup(self, soup):
        wave_directions = self.parse_wave_directions(soup)
        wind_directions = self.parse_wind_directions(soup)
        total_records = len(wave_directions)
        spot_name = self.parse_spot_name(soup)

        data = {
            "date": self.parse_dates_str(soup, total_records),
            "time": self.parse_hour_intervals(soup),
            "wave_direction": wave_directions,
            "wind_direction": wind_directions,
            "wind_status": self.parse_windstatus(wave_directions, wind_directions),
            "wave_period": self.parse_wave_periods(soup),
            "wave_height": self.parse_wave_heights(soup),
            "wind_speed": self.parse_wind_speeds(soup),
            "spot_name": self.parse_spot_names(spot_name, total_records),
        }

        return pd.DataFrame(data)

    def process_soup(self, soup):
        df = self.get_dataframe_from_soup(soup)
        return self.format_dataframe(df)

    def scrape(self, url):
        response = self.beach_request(url)
        soup = BeautifulSoup(response.text, "html.parser")
        return self.process_soup(soup)
