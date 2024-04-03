from bs4 import BeautifulSoup
import os, datetime, polars as pl
from typing import Dict
from requests import Session
from utils import get_day_name, datestr_to_datetime
from datetime import datetime, timedelta


class TidesScraper(object):
    def __init__(self):
        self.link = (
            "https://www.temperaturadelmar.es/europa/lanzarote/arrecife/tides.html"
        )

        self.headers = {
            "authority": "www.temperaturadelmar.es",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "es-ES,es;q=0.9",
            "cookie": "_ctpuid=7b356183-ddee-4fc8-94d5-7963df085d5d",
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
        self.session = Session()

    def scrape_graph(self) -> Dict:
        response = self.session.get(url=self.link, headers=self.headers)
        tides = {
            "datetime": [],
            "tide": [],
        }
        s = BeautifulSoup(response.text, "html.parser")
        tables = s.select("table.table.table-bordered")
        days_string = [day_h3.text for day_h3 in s.select("h3")][2:]
        for table, day_string in zip(tables, days_string):
            format_day = "%A %d %B %Y"
            tide_date = datestr_to_datetime(day_string, format_day).date()
            tablebody = table.find("tbody")
            rows = tablebody.find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                for cell in cells:
                    if cell.text == "pleamar" or cell.text == "bajamar":
                        current_sea_state = cell.text
                        tides["tide"].append(current_sea_state)
                    elif ":" in cell.text:
                        format_time = "%H:%M"
                        tide_time = datestr_to_datetime(cell.text, format_time).time()
                        tide_datetime = datetime.combine(tide_date, tide_time)
                        tides["datetime"].append(tide_datetime)
        return tides
        # return pl.DataFrame(tides)

    def scrape_table(self) -> Dict:
        response = self.session.get(url=self.link, headers=self.headers)
        hours_dict = {}
        s = BeautifulSoup(response.text, "html.parser")
        tables = s.find_all("table", class_="table table-bordered")
        horas = []
        for table in tables:
            tablebody = table.find("tbody")
            rows = tablebody.find_all("tr")
            hora = []
            for row in rows:
                cells = row.find_all("td")
                for cell in cells:
                    if cell.text == "pleamar" or cell.text == "bajamar":
                        hora.append(cell.text.replace("amar", ""))
                    elif ":" in cell.text:
                        ple_baj = hora.pop()
                        text_to_insert = f"{ple_baj} {cell.text}h"
                        hora.insert(len(hora), text_to_insert)
            horas.append(hora)
            for hora in horas:
                if len(hora) == 3:
                    hora.append(None)
        for hora in horas:
            hours_dict[get_day_name(horas.index(hora))] = hora
        return pl.DataFrame(hours_dict)

    def construct_month_tides(self, tides: dict) -> list:
        tide_interval = timedelta(hours=6, minutes=12, seconds=30)

        current_time = tides.get("datetime")[-1]
        current_tide = tides.get("tide")[-1]
        start_datetime = current_time
        while current_time <= start_datetime + timedelta(days=15):
            tides.get("datetime").append(current_time)
            tides.get("tide").append(current_tide)
            current_time += tide_interval
            current_tide = "pleamar" if current_tide == "bajamar" else "bajamar"
        return tides

    def tasks(self):
        tides = self.scrape_graph()
        return self.construct_month_tides(tides)
