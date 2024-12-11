from bs4 import BeautifulSoup
from typing import Dict
import polars as pl
from utils import (
    rename_key,
    generate_tides,
    generate_nearest_tides,
    generate_tide_percentages,
    generate_energy,
    render_html,
    generate_datetimes,
    filter_spot_dataframe,
    create_date_name_column,
    create_direction_predominant_column,
    generate_spot_names,
    datestr_to_frontend_format,
)
import re
from APIS.discord_api import DiscordBot
import locale
import requests

locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")


class Windguru(object):
    def __init__(self):
        pass

    def beach_request(self, url):
        r_text = render_html(url=url, tag_to_wait="table.tabulka", timeout=60 * 1000)
        return BeautifulSoup(r_text, "html.parser")

    def format_forecast(self, forecast: Dict, tides: dict) -> Dict:
        forecast = rename_key(forecast, "tabid_0_0_dates", "datetime")
        forecast = rename_key(forecast, "tabid_0_0_SMER", "wind_direction_raw")
        forecast = rename_key(forecast, "tabid_0_0_HTSGW", "wave_height")
        forecast = rename_key(forecast, "tabid_0_0_DIRPW", "wave_direction_raw")
        forecast = rename_key(forecast, "tabid_0_0_PERPW", "wave_period")
        forecast = rename_key(forecast, "tabid_0_0_WINDSPD", "wind_speed")
        forecast = rename_key(forecast, "tabid_0_0_TMPE", "temperature")

        forecast["wind_direction"] = [
            self.parse_text_from_text(element)
            for element in forecast["wind_direction_raw"]
        ]
        forecast["wave_direction"] = [
            self.parse_text_from_text(element)
            for element in forecast["wave_direction_raw"]
        ]
        forecast["wind_direction_degrees"] = [
            self.parse_number_from_text(element)
            for element in forecast["wind_direction_raw"]
        ]
        forecast["wave_direction_degrees"] = [
            self.parse_number_from_text(element)
            for element in forecast["wave_direction_raw"]
        ]

        forecast["date"] = [
            datestr_to_frontend_format(dt.split(".")[0]) for dt in forecast["datetime"]
        ]
        forecast["time"] = [
            dt.split(".")[1].replace("h", ":00") for dt in forecast["datetime"]
        ]
        forecast["datetime"] = generate_datetimes(forecast["date"], forecast["time"])

        forecast["wave_period"] = self.format_dict_digit_all_values(
            forecast, "wave_period", "int"
        )
        forecast["wave_height"] = self.format_dict_digit_all_values(
            forecast, "wave_height", "float"
        )
        forecast["wind_speed"] = self.format_dict_digit_all_values(
            forecast, "wind_speed", "float"
        )
        forecast["tide"] = generate_tides(tides, forecast["datetime"])
        forecast["nearest_tide"] = generate_nearest_tides(tides, forecast["datetime"])
        forecast["tide_percentage"] = generate_tide_percentages(
            tides, forecast["datetime"]
        )
        forecast["energy"] = generate_energy(
            forecast["wave_height"], forecast["wave_period"]
        )
        forecast["date_name"] = create_date_name_column(forecast["datetime"])
        forecast["wind_direction_predominant"] = create_direction_predominant_column(
            forecast["wind_direction_degrees"]
        )
        forecast["wave_direction_predominant"] = create_direction_predominant_column(
            forecast["wave_direction_degrees"]
        )
        forecast["spot_name"] = generate_spot_names(forecast)
        return forecast

    def get_dataframe_from_soup(self, soup: BeautifulSoup, tides: dict) -> Dict:
        forecast = {}
        table = soup.find("table", class_="tabulka")
        tablebody = table.find("tbody")
        rows = tablebody.find_all("tr")

        if len(rows) == 0:
            print(soup)
            raise Exception("No se encontro la tabla")

        for row in rows:
            cells = row.find_all("td")
            id = row["id"]
            if id in [
                "tabid_0_0_SMER",
                "tabid_0_0_dates",
                "tabid_0_0_HTSGW",
                "tabid_0_0_DIRPW",
                "tabid_0_0_PERPW",
                "tabid_0_0_WINDSPD",
                "tabid_0_0_TMPE",
            ]:
                forecast[id] = []
                for cell in cells:
                    if ("SMER" in id) | ("DIRPW" in id):
                        try:
                            value = cell.select("span")[0]["title"]
                        except Exception as e:
                            value = "NAN (-69°)"
                    else:
                        value = cell.get_text().replace("-", "-69")
                    forecast[id].append(value)
        if forecast != {}:
            total_records = len(max(forecast.items(), key=lambda item: len(item[1]))[1])
            forecast = self.format_forecast(forecast, tides)
            return pl.DataFrame(forecast)
        return pl.DataFrame()

    def parse_text_from_text(self, text):
        return text.split(" ")[0].replace("O", "W")

    def parse_number_from_text(self, text):
        pattern = r"(\d+)°"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1))

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

    def windguru_request(self):
        import requests

        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "es-ES,es;q=0.9",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            # 'Cookie': 'langc=es-; deviceid=9ec2d8a3c0ef8b0d0a8281e69cf4a8fb; _sharedID=1bc832d1-5973-44e9-a1f9-56075be8bdcd; snconsent=eyJwdWJsaXNoZXIiOjAsInZlbmRvciI6MywiZ2xDb25zZW50cyI6IiIsImN2Q29uc2VudHMiOnt9fQ.AlMAKwAuADcAPQBGAFMAWQBdAGwAdQB6AHwAhwCPAJAAkwCVAJ8AwADEANMA5ADmAO8BAwEKAR4BIwE3AT4BQAFCAUMBRwFvAXMBgQGKAY0BlwGfAagBrgG0Ab0BxQHmAesB7gHvAgoCCwIcAiYCLwIwAjgCPgJAAkgCSwJPAuEDIgMjAzQDNQNHA2ADgwOIA5oDowOqA9MD1QPZA-sEAwQHBBAEFgQbBB0EKwREBEcESQRLBFMEbwR3BH0EgASKBI4EogSkBLUEvwTKBMsEzgTkBPQE9gT8BQQFCgUVBRsFIAVBBUwFVAVfBXsFhwWIBY0FjwWgBakFrwXXBegF7AX1BgQGDAYTBhYGIgYpBisGLwYwBjcGQwZQBmYGcwZ1BnsGgwaNBo4GkgahBqMGpwawBrQGuQa9BsQG0QbWBuUG9gb6BwgHEgchByMHKAcuBzAHMgczBzUHQwdKB04HVgdYB2EHawd9B4kHlgeYB6oHqwesB68HsAexB7oHwQfDB9MH2AfrB_MH9wf_CAQICAgQCBQIGAgaCCgIKgg3CDsIPQhDCEwIUghVCFcIWQhcCGMIZghsCHYIgQiHCIoInQilCKgIqwisCK4IsQi6CM0I5wjqCPQJAQkFCQgJDAkSCRUJGAkbCR4JHwkgCSEJJwkyCTUJNgk3CUIJSAlJCVMJYAljCWUJZwlrCW4JcAlyCXkJiAmPCZ0JoQmkCagJrQmxCbQJtgm4Cb0JwgnFCc4J1QneCd8J5AnnCe4J-AoDCgQKBwoICgkKCwoMCg8KEQoXChgKJAosCi0KMAoxCjIKNAo2Cj0KRApFCkkKTApSClMKVQpWCloKWwpcCmAKYQpiCmQKZQptCm4KdQp5CnwKfwqCCocKigqZCpoKqQqzCs8K0ArSCtQK4ArjCucK6AruCvEK9Qr8Cv0LAAsBCwULBgsLCw4LDwsSCxYLFwscCx4LIQsiCyQLJgssCy4LLwsxCzMLNQs5CzoLOws8Cz4LQAtBC0ILQwtEC0YLRwtIC0kLSwtNC04LTwtRC1ILVAtVC1wLXQtkC2ULZgtnC2gLagtrC28LcQtyC3MLfAt9C4MLhQuGC4wLjguRC5MLlAuVC5YLmAudC58LowukC6ULpwupC6oLqwuyC7MLtQu3C7gLugu7C70LwAvBC8ILxAvIC8kLygvLC9EL1AvaC94L4wvoC-wL7QvvC_IL8wv3C_oL_Av-DAEMAgwDDAQMBQwRDBIMFQwWDBcMGQwbDBwMIgwlDCgMLQwvDDYMNww4DDoMPwxADEkMTgxPDFIMUwxbDF8MZAxlDG4MbwxwDHEMcwx0DHUMdgx6DHwMiQyKDIsMjgyPDJEMkwyWDJcMmQyaDJsMnAyeDJ8MogyjDKQMpQymDKgMrAytDLIMswy1DLkMvAzGDMgM0QzYDNoM3AzdDOAM4wzkDOoM6wztDPIM8wz0DPYM_A0ADQINAw3LDpMO9xAjEbMSFxJ7Et8UbxsTHEMelx77IuMmAyf3KYcqTysXLQsyHzVANaM3nTf8PXNBv0IjUvFZ92SDZUtlr2jPbFNst21_cDtwn3O_e49_E4NfhbeHRw; euconsent-v2=CQHqmJgQHqmJgDlBWAESBIFsAP_gAEPgAATIKdNV_G__bXlv-X736ftkeY1f9_h77sQxBhfJs-4FzLvW_JwX32EzNE36tqYKmRIAu3bBIQNtGJjUTVChaogVrzDsaE2coTtKJ-BkiHMRc2dYCF5vm4tj-QKZ5vr_91d52R_t7dr-3dzyz5Vnv3a9_-b1WJidK5-tH_v_bROb-_I-9_x-_4v8_N_rE2_eT1t_tWvt739-8tv___f99___________3_-__wU6AJMNCogDLAkJCDQMIIEAKgrCAigQAAAAkDRAQAmDAp2BgEusJEAIAUAAwQAgABRkACAAACABCIAIACgQAAQCBQABgAQDAQAEDAACACwEAgABAdAxTAggUCwASMyIhTAhCASCAlsqEEgCBBXCEIs8AiAREwUAAAAABWAAICwWBxJICVCQQJcQbQAAEACAQQAFCCTkwABAGbLUHgybRlaYBo-YJENMAyAAAA; _ga=GA1.1.1673142863.1730893842; _cc_id=bf375ae509a9208d26c6b2bf1d48187b; _lr_env_src_ats=false; wgcookie=2|||||||||49328||||0|51_0|0|||||||||; ac_cclang=; ac_user_id=acux44vc5752g4872a056f7e24c031d69e605be162ca38bf3d79d676204583d4dfbee9f08beb43c; _au_1d=AU1D-0100-001731523718-L3O7HRF7-Q0AG; _au_last_seen_iab_tcf=1731523718003; _pbjs_userid_consent_data=3524755945110770; _sharedID_cst=JizbLCcsIA%3D%3D; panoramaId_expiry=1733926176381; panoramaId=c3b9cf7059d83a4d9716af5d79f9c8bd038aea7607ab7e50f6f0e15ae75d3161; panoramaIdType=panoIndiv; _sharedID_last=Mon%2C%2009%20Dec%202024%2012%3A51%3A36%20GMT; _ga_2NEY9YDWMB=GS1.1.1733748696.107.0.1733748696.0.0.0; cto_bundle=UKMKKV8wRU05aEp6T29IalglMkZRN1JSQXp2VllVVjhRNiUyQmlkVURLdTJPMFpyRUJvT1ZOTGpiWkZxdDJ3OUJMeVBzNSUyQnBXc3YzJTJCSk5KQSUyQnIlMkJ0SWFHRXBTdWdVMHpGS2tURkFLY2dwcnBnRkdCRmt6eDhOYzVMaTFaU3dDalJYQWtlQ3lneDVPa29uZ0dra1U1SnJBWUUlMkZBa2tHdyUzRCUzRA; __gads=ID=f91c4f474cf41d42:T=1730893845:RT=1733749327:S=ALNI_MYMXr2q4NU1CaVzAhcMS7eE78gfIw; __gpi=UID=00000f6be5ad9fcd:T=1730893845:RT=1733749327:S=ALNI_MbAz8LNc8YTVV96sViwvjL760b5NQ; __eoi=ID=b592dec7ba13116a:T=1730893845:RT=1733749327:S=AA-AfjbAHKdOWULGMncMuL7MhWgx; session=483c20522a93ea0d0b1ba9be469a29c4',
            "Referer": "https://www.google.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
        }

        return requests.get("https://www.windguru.cz/49328", headers=headers)

    def scrape(self, url, tides):
        soup = self.beach_request(url)
        return self.get_dataframe_from_soup(soup, tides)
