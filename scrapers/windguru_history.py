import requests
import json
from bs4 import BeautifulSoup
from functools import reduce
from typing import Dict
import polars as pl
from utils import (
    rename_key,
    generate_tides,
    generate_nearest_tides,
    generate_tide_percentages,
    generate_energy,
    open_browser,
    generate_datetimes,
    filter_spot_dataframe,
    from_direction_degrees_to_cardinal,
)
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
from APIS.discord_api import DiscordBot

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class WindguruHistory(object):
    def __init__(self):
        self.session = requests.Session()
        self.browser = open_browser()

    def process_browser_log_entry(self, entry):
        response = json.loads(entry["message"])["message"]
        return response

    def obtain_requests(self):
        browser_log = self.browser.get_log("performance")
        return [self.process_browser_log_entry(entry) for entry in browser_log]

    def remove_headless(self, text: str) -> str:
        return re.sub(r"headless", "", text, flags=re.IGNORECASE)

    def process_headers(self, headers: dict) -> dict:
        processed_headers = {}
        for key, value in headers.items():
            processed_value = self.remove_headless(value)
            processed_headers[key] = processed_value
        return processed_headers

    def capture_headers_for_url(self, url: str) -> dict:
        all_requests = self.obtain_requests()
        headers = self.capture_headers_for_chrome(all_requests, url)
        return self.process_headers(headers)

    def capture_headers_for_chrome(self, all_requests: list, url: str) -> dict:
        for message in all_requests:
            message_params = message["params"]
            if message["method"] == "Network.requestWillBeSent":
                request = message_params["request"]
                if request["url"] == url:
                    headers = request["headers"]
                    return headers

    def retrieve_cookies_dict(self) -> Dict:
        return {
            cookie["name"]: cookie["value"] for cookie in self.browser.get_cookies()
        }

    def add_cookies_to_requests_session(self):
        cookies_dict = self.retrieve_cookies_dict()
        for cookie_key, cookie_value in cookies_dict.items():
            self.session.cookies.set(cookie_key, cookie_value)
        return

    def submit_login_form(self) -> None:
        username_css_selector = "input#inputusername"
        # TODO meterlo en variables de entorno
        # TODO mirar si puedo quitarle el selenium para el login
        usnm = "bodyboard69"
        password_name = "password"
        pwd = "b0dyb04rd"
        submit_button_css_selector = "button.akce.wide"

        wait = WebDriverWait(self.browser, 10)
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, submit_button_css_selector)
            )
        )
        usnm_element = self.browser.find_element(By.CSS_SELECTOR, username_css_selector)
        usnm_element.send_keys(str(usnm))

        password_input = self.browser.find_element(By.NAME, password_name)
        password_input.send_keys(str(pwd))

        submit_element = self.browser.find_element(
            By.CSS_SELECTOR, submit_button_css_selector
        )
        submit_element.click()
        element = WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table.tabulka"))
        )
        assert element

    def history_daterange_request(self, headers, start_date, end_date):
        FAMARA_ID = 49328

        data = {
            "date_from": start_date,  # "2024-07-01",
            "date_to": end_date,  # "2024-08-01",
            "step": "2",
            "min_use_hr": "6",
            "pwindspd": "1",
            "psmer": "1",
            "phtsgw": "1",
            "pwavesmer": "1",
            "pperpw": "1",
            "id_spot": FAMARA_ID,
            "id_model": "3",
            "id_stats_type": "",
        }

        response = self.session.post(
            "https://www.windguru.cz/ajax/ajax_archive.php", headers=headers, data=data
        )
        return BeautifulSoup(response.text, "html.parser")

    # TODO hacer una clase y archivo solo de selenium
    def windguru_tasks(self):
        login_url = "https://www.windguru.cz/login.php"
        try:
            self.browser.get(login_url)
            self.submit_login_form()
            archive_url = "https://www.windguru.cz/archive.php"
            self.browser.get(archive_url)
            self.add_cookies_to_requests_session()
            headers = self.capture_headers_for_url(archive_url)
            soup = self.history_daterange_request(headers, "2022-11-01", "2022-12-01")
            return soup
        except Exception as e:
            raise e
        finally:
            self.browser.close()
            self.browser.quit()

    def beach_request(self, url):
        FAMARA_ID = 49328

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:129.0) Gecko/20100101 Firefox/129.0",
            "Accept": "text/html, */*; q=0.01",
            "Accept-Language": "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": f"https://www.windguru.cz/archive.php?id_spot={FAMARA_ID}&id_model=3&date_from=2024-07-25&date_to=2024-08-25",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://www.windguru.cz",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Connection": "keep-alive",
            "Priority": "u=0",
        }

        data = {
            "date_from": "2024-07-25",
            "date_to": "2024-08-25",
            "step": "2",
            "min_use_hr": "6",
            "pwindspd": "1",
            "psmer": "1",
            "ptmp": "1",
            "id_spot": FAMARA_ID,
            "id_model": "3",
            "id_stats_type": "",
        }

        response = requests.post(
            "https://www.windguru.cz/ajax/ajax_archive.php", headers=headers, data=data
        )

        # r_text = render_html(url=url, tag_to_wait="table.tabulka", timeout=60 * 1000)
        # return BeautifulSoup(r_text, "html.parser")

    def do_date_match_regex(self, date):
        match = re.search(r"\d{2}\.\d{2}\.\d{4}", date.text)
        if match:
            return True
        return False

    def format_dates(self, dates):
        dates = list(filter(self.do_date_match_regex, dates))
        dates = [date.text for date in dates]
        return dates

    def scrape_dates(self, soup):
        dates = soup.select("tr > td > b")
        return self.format_dates(dates)

    def extend_hours(self, hours, dates_length):
        return hours * dates_length

    def extend_dates(self, hours, hours_length):
        return [item for item in hours for _ in range(hours_length)]

    def scrape_hours(self, soup):
        all_rows = soup.select("tr")
        hours_row = all_rows[0].select("tr")[1]
        hours = list(set([i.text.strip() for i in hours_row if i.text.strip() != ""]))
        sorted_hours = self.sort_hours(hours)
        return sorted_hours

    def format_cell(self, cell):
        return cell.text.strip()

    def svg_to_direction(self, svg_angle):
        normalized_angle = svg_angle % 360
        direction = (normalized_angle - 180) % 360
        return direction if direction != 0 else 360

    def divide_list_by_group_length(self, input_list, group_length):
        num_groups = len(input_list) // group_length + (
            1 if len(input_list) % group_length != 0 else 0
        )
        groups = []
        for i in range(num_groups):
            start_index = i * group_length
            end_index = start_index + group_length
            groups.append(input_list[start_index:end_index])

        return groups

    def sort_hours(self, hours: list):
        return sorted(hours, key=lambda x: datetime.strptime(x, "%Hh").time())

    def parse_rotate(self, transform):
        match = re.search(r"rotate\((\d+),", transform)
        if match:
            number = match.group(1)
            return int(number)

    def scrape_wind_speed(self, soup, position):
        wind_speeds = []
        all_rows = soup.select("tr")
        rows = all_rows[3:]

        hours_row = all_rows[0].select("tr")[1]
        hours = list(set([i.text.strip() for i in hours_row if i.text.strip() != ""]))
        sorted_hours = self.sort_hours(hours)

        for row in rows:
            cells = row.select("td")[1:]
            wind_speeds += cells[: len(sorted_hours)]
        wind_speeds = [
            int(self.format_cell(wind_speed))
            for wind_speed in wind_speeds
            if wind_speed != ""
        ]
        return wind_speeds

    def scrape_wave_period(self, soup, position):
        wave_periods = []
        all_rows = soup.select("tr")
        rows = all_rows[3:]

        hours_row = all_rows[0].select("tr")[1]
        hours = list(set([i.text.strip() for i in hours_row if i.text.strip() != ""]))
        sorted_hours = self.sort_hours(hours)

        for row in rows:
            cells = row.select("td")[1:]
            wave_periods += cells[-len(sorted_hours) :]
        wave_periods = [
            int(self.format_cell(wave_period))
            for wave_period in wave_periods
            if self.format_cell(wave_period) != ""
            and self.format_cell(wave_period) != "-"
        ]
        return wave_periods

    def scrape_wave_height(self, soup, position):
        wave_heights = []
        all_rows = soup.select("tr")
        rows = all_rows[3:]

        hours_row = all_rows[0].select("tr")[1]
        hours = list(set([i.text.strip() for i in hours_row if i.text.strip() != ""]))
        sorted_hours = self.sort_hours(hours)

        for row in rows:
            cells = row.select("td")[1:]
            wave_heights += cells[
                (position - 1) * len(sorted_hours) : (position) * len(sorted_hours)
            ]
        wave_heights = [
            float(self.format_cell(wave_height))
            for wave_height in wave_heights
            if self.format_cell(wave_height) != ""
            and self.format_cell(wave_height) != "-"
        ]
        return wave_heights

    def scrape_wind_direction(self, soup, position):
        scrapped_wind_directions = []
        wind_directions = []
        all_rows = soup.select("tr")
        rows = all_rows[3:]

        hours_row = all_rows[0].select("tr")[1]
        hours = list(set([i.text.strip() for i in hours_row if i.text.strip() != ""]))
        sorted_hours = self.sort_hours(hours)

        for row in rows:
            cells = row.select("td")[1:]
            wind_directions += cells[len(sorted_hours) : position * len(sorted_hours)]
        for wind_direction in wind_directions:
            svg_g = wind_direction.select("svg > g")
            if len(svg_g) > 0:
                transform = svg_g[0]["transform"]
                rotate = self.parse_rotate(transform)
                direction = int(self.svg_to_direction(rotate))
            else:
                direction = None
            scrapped_wind_directions.append(direction)
        return scrapped_wind_directions

    def scrape_wave_direction(self, soup, position):
        # TODO refactorizar con wind_direction
        scrapped_wave_directions = []
        wave_directions = []
        all_rows = soup.select("tr")
        rows = all_rows[3:]

        hours_row = all_rows[0].select("tr")[1]
        hours = list(set([i.text.strip() for i in hours_row if i.text.strip() != ""]))
        sorted_hours = self.sort_hours(hours)

        for row in rows:
            cells = row.select("td")[1:]
            wave_directions += cells[
                (position - 1) * len(sorted_hours) : position * len(sorted_hours)
            ]
        for wave_direction in wave_directions:
            svg_g = wave_direction.select("svg > g")
            if len(svg_g) > 0:
                transform = svg_g[0]["transform"]
                rotate = self.parse_rotate(transform)
                direction = int(self.svg_to_direction(rotate))
            else:
                direction = None
            scrapped_wave_directions.append(direction)
        return scrapped_wave_directions

    def get_dataframe_from_soup(self, soup: BeautifulSoup) -> Dict:
        forecast = {}
        unique_dates = self.scrape_dates(soup)
        sorted_hours = self.scrape_hours(soup)
        len_sorted_hours = len(sorted_hours)
        hours = self.extend_hours(sorted_hours, len(unique_dates))
        dates = self.extend_dates(unique_dates, len_sorted_hours)
        wind_speed = self.scrape_wind_speed(soup, 1)
        wind_direction_degrees = self.scrape_wind_direction(soup, 2)
        wave_height = self.scrape_wave_height(soup, 3)
        wave_direction_degrees = self.scrape_wave_direction(soup, 4)
        wave_period = self.scrape_wave_period(soup, 5)
        forecast["dates"] = dates
        forecast["hours"] = hours
        forecast["wind_speed"] = wind_speed
        forecast["wind_direction"] = [
            from_direction_degrees_to_cardinal(direction)
            for direction in wind_direction_degrees
        ]
        forecast["wave_height"] = wave_height
        forecast["wave_direction"] = [
            from_direction_degrees_to_cardinal(direction)
            for direction in wave_direction_degrees
        ]
        forecast["wave_period"] = wave_period
        forecast["wind_direction_degrees"] = wind_direction_degrees
        forecast["wave_direction_degrees"] = wave_direction_degrees
        forecast["energy"] = generate_energy(wave_height, wave_period)

        return pl.DataFrame(forecast)

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

    def remove_rows_with_none(self, df: pl.DataFrame) -> pl.DataFrame:
        masks = [df[col].is_not_null() for col in df.columns]

        # Combine all the masks using logical AND to create a single mask
        combined_mask = reduce(lambda x, y: x & y, masks)

        # Filter the DataFrame using the combined mask
        return df.filter(combined_mask)

    def scrape(self):
        soup = self.windguru_tasks()
        df = self.get_dataframe_from_soup(soup)
        df = self.remove_rows_with_none(df)
        return df


# TODO si una celda es none, quitar toda esa fila en la misma posicion para todas las listas
