import re
from datetime import datetime, timedelta
from typing import Dict, List

import polars as pl
from bs4 import BeautifulSoup
from curl_cffi import Session


class TidesScraperLanzarote:
    def __init__(self):
        # URL específica de Arrecife, Lanzarote
        self.link = "https://tablademareas.com/es/islas-canarias/arrecife-lanzarote"
        self.session = Session()

    def _clean_text(self, text: str) -> str:
        return text.replace("h", "").strip()

    def scrape_tides(self) -> List[Dict]:
        response = self.session.get(url=self.link, impersonate="chrome131")
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        tides_data = []
        rows = soup.find_all("tr", class_=re.compile(r"tabla_mareas_fila_fondo"))

        for row in rows:
            onclick = row.get("onclick", "")
            date_match = re.search(r"(\d{4}-\d{2}-\d{1,2})", onclick)

            if not date_match:
                continue

            current_date_str = date_match.group(1)
            marea_cells = row.find_all("td", class_="tabla_mareas_marea")

            for cell in marea_cells:
                hora_div = cell.find("div", class_="tabla_mareas_marea_hora")
                if not hora_div or not hora_div.text.strip():
                    continue
                hora_raw = hora_div.text.replace("h", "").strip()

                tipo_div = cell.find("div", class_="tabla_mareas_marea_bajamar_pleamar")
                tipo = (
                    "bajamar"
                    if "tabla_mareas_marea_bajamar" in tipo_div.get("class", [])
                    else "pleamar"
                )

                altura_span = cell.find(
                    "span", class_="tabla_mareas_marea_altura_numero"
                )
                altura = altura_span.text.replace(",", ".") if altura_span else "0"
                full_dt = datetime.strptime(
                    f"{current_date_str} {hora_raw}", "%Y-%m-%d %H:%M"
                )

                tides_data.append(
                    {
                        "tide": tipo,
                        "timestamp": full_dt.timestamp(),
                        "height": float(altura),
                        "datetime": full_dt.isoformat(),
                    }
                )
        tides_data.sort(key=lambda x: x["timestamp"])
        return tides_data

    def construct_future_tides(
        self, tides: List[Dict], days_to_extend: int = 15
    ) -> List[Dict]:
        if not tides:
            return []

        tide_interval = timedelta(hours=6, minutes=12, seconds=30)
        last_tide = tides[-1]

        current_ts = last_tide["timestamp"]
        current_type = last_tide["tide"]
        limit_ts = current_ts + (days_to_extend * 86400)

        while current_ts < limit_ts:
            current_ts += tide_interval.total_seconds()
            current_type = "pleamar" if current_type == "bajamar" else "bajamar"

            tides.append(
                {
                    "tide": current_type,
                    "timestamp": current_ts,
                    "height": None,
                    # Convertimos a string ISO para que sea serializable en JSON
                    "datetime": datetime.fromtimestamp(current_ts).isoformat(),
                }
            )
        return tides

    def get_tides_dataframe(self, tides: List[Dict]) -> pl.DataFrame:
        return pl.DataFrame(tides)

    def tasks(self):
        tides = self.scrape_tides()
        tides = self.construct_future_tides(tides)
        unique_tides = {t["timestamp"]: t for t in tides}.values()
        return sorted(list(unique_tides), key=lambda x: x["timestamp"])
