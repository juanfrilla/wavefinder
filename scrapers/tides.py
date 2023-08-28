from bs4 import BeautifulSoup
import os, datetime, pandas as pd
from typing import Dict
from requests import Session
from utils import get_day_name

# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service


class TidesScraper(object):
    def __init__(self):
        # options = webdriver.ChromeOptions()
        # options.add_argument("--headless")
        # options.add_argument("--start-maximized")
        # ser = Service(r"/usr/bin/chromedriver")
        # self.driver = webdriver.Chrome(service=ser, options=options)
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

    def scrape(self) -> Dict:
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
                    if (
                        cell.text == "pleamar" or cell.text == "bajamar"
                    ):  # TODO poner aqui directamente subiendo hasta las o bajando hasta las
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
        return pd.DataFrame(hours_dict)

    def mareas_to_df(self, dict: Dict) -> pd.DataFrame:
        df = pd.DataFrame(dict)
        return df

    def df_to_txt(self, df: pd.DataFrame) -> None:
        if os.path.exists("mareas.txt"):
            os.remove("mareas.txt")
        with open("mareas.txt", "a") as f:
            dfAsString = df.to_string(header=True, index=False)
            f.write(dfAsString)


if __name__ == "__main__":
    scraper = TidesScraper()
    x = scraper.scrape()

    print()
