import requests
from models.surfline import Wave, Wind, Tide, Rating, Item
import pandas as pd


class Surfline:
    def __init__(self):
        self.headers = {
            "authority": "services.surfline.com",
            "accept": "*/*",
            "accept-language": "es-ES,es;q=0.9",
            "if-none-match": 'W/"ef8-IZmhX4hvYIcQxvgeKdigAvBS8BE"',
            "origin": "https://www.surfline.com",
            "referer": "https://www.surfline.com/",
            "sec-ch-ua": '"Chromium";v="112", "Google Chrome";v="112", "Not:A-Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
        }

    def wind_request(self, spot_id):
        params = {
            "spotId": spot_id,
            "days": "5",
            "intervalHours": "1",
            "corrected": "false",
        }

        response = requests.get(
            "https://services.surfline.com/kbyg/spots/forecasts/wind",
            params=params,
            headers=self.headers,
        )

        return response.json()

    def wave_request(self, spot_id):
        params = {
            "spotId": spot_id,
            "days": "5",
            "intervalHours": "1",
        }

        response = requests.get(
            "https://services.surfline.com/kbyg/spots/forecasts/wave",
            params=params,
            headers=self.headers,
        )

        return response.json()

    def conditions_request(
        self,
    ):
        params = {
            "subregionId": "58581a836630e24c448790e0",
            "days": "5",
        }

        response = requests.get(
            "https://services.surfline.com/kbyg/regions/forecasts/conditions",
            params=params,
            headers=self.headers,
        )

        return response.json()

    def rating_request(self, spot_id):
        params = {
            "spotId": spot_id,
            "days": "5",
            "intervalHours": "1",
        }

        response = requests.get(
            "https://services.surfline.com/kbyg/spots/forecasts/rating",
            params=params,
            headers=self.headers,
        )

        return response.json()

    def tides_request(self, spot_id):
        params = {
            "spotId": spot_id,
            "days": "5",
        }

        response = requests.get(
            "https://services.surfline.com/kbyg/spots/forecasts/tides",
            params=params,
            headers=self.headers,
        )

        return response.json()

    def format_dataframe(self, df):
        df = df.drop(
            df[
                (df["time"] == "20:00:00")
                | (df["time"] == "21:00:00")
                | (df["time"] == "22:00:00")
                | (df["time"] == "23:00:00")
                | (df["time"] == "00:00:00")
                | (df["time"] == "01:00:00")
                | (df["time"] == "02:00:00")
                | (df["time"] == "03:00:00")
                | (df["time"] == "04:00:00")
                | (df["time"] == "05:00:00")
            ].index
        )
        
        df = df[df["wave_height"] != 0.0]
        return df

    def scrape(self, url):
        spot_id = url.split("/")[-1].replace("?view=table", "")
        location = url.split("/")[-2]
        wave_info = self.wave_request(spot_id)
        waves = wave_info.get("data", {}).get("wave", [])
        wind_info = self.wind_request(spot_id)
        winds = wind_info.get("data", {}).get("wind", [])
        tides_info = self.tides_request(spot_id)
        tides = tides_info.get("data", {}).get("tides", [])
        rating_info = self.rating_request(spot_id)
        ratings = rating_info.get("data", {}).get("rating", [])
        combined_data = []
        for wave, wind, tide, rating in zip(waves, winds, tides, ratings):
            wave_item = Wave(**wave)
            wind_item = Wind(**wind)
            tide_item = Tide(**tide)
            rating_item = Rating(**rating)
            item = Item(
                date_name=wave_item.date_name,
                date=wave_item.date,
                time=wave_item.time,
                wind_direction=wind_item.wind_direction,
                wind_description=wind_item.wind_description,
                wind_status=wind_item.directionType,
                wind_speed=wind_item.speed,
                wave_direction=wave_item.swell_direction,
                wave_period=wave_item.period,
                wave_height=wave_item.swell_size,
                tide_height=tide_item.height,
                tide_state=tide_item.type,
                spot_name=location,
                page_rating=rating_item.rating_key,
                approval=Item.calculate_approval(
                    wind_item.wind_direction, wave_item.period, wave_item.swell_size
                ),
            ).model_dump()
            combined_data.append(item)
        df = pd.DataFrame(combined_data)
        # return df
        return self.format_dataframe(df)
