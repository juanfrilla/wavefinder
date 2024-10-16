import re, json, math
from bs4 import BeautifulSoup
from requests import Response
import polars as pl
from datetime import datetime, date, time, timedelta
from dateutil.relativedelta import relativedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Dict

MONTH_MAPPING = {
    "Ene": "01",
    "Feb": "02",
    "Mar": "03",
    "Abr": "04",
    "May": "05",
    "Jun": "06",
    "Jul": "07",
    "Ago": "08",
    "Sep": "09",
    "Oct": "10",
    "Nov": "11",
    "Dic": "12",
}
INTERNAL_DATE_STR_FORMAT = "%d/%m/%Y"
INTERNAL_TIME_STR_FORMAT = "%H:%M:%S"
FRONT_END_DATE_FORMAT = "%A, %d de %B de %Y"

CONTRARIES = {"N": "S", "S": "N", "E": "W", "W": "E"}


def calculate_energy(wave_height: float, wave_period: float):
    return math.ceil(1 / 2 * 9.81 * wave_height**2 * wave_period)


def generate_energy(wave_heights: list, wave_periods: list):
    return [
        calculate_energy(wave_height, wave_period)
        for wave_height, wave_period in zip(wave_heights, wave_periods)
    ]


def generate_date_range(start_date: datetime, end_date: datetime):
    date_list = []
    current_date = start_date

    while current_date <= end_date:
        date_list.append(current_date.strftime("%d/%m/%Y"))
        current_date += timedelta(days=1)

    return date_list


# TODO posiblemente hacer una clase para todo esto, para calcular los spot_names
# TODO quitar float de donde no sea necesario, poner int


def punta_mujeres_conditions(
    wind_direction_predominant: str,
    wave_direction_predominant: str,
    wind_direction: str,
    wave_direction: str,
    wave_energy: int,
):
    punta_mujeres_wave_directions = ["N", "NE", "E", "NNW", "NNE", "NW"]
    unwanted_wave_directions = ["WNW"]
    if (
        punta_mujeres_favorable_wind(wind_direction_predominant, wind_direction)
        & (
            (wave_direction_predominant in punta_mujeres_wave_directions)
            | (wave_direction in punta_mujeres_wave_directions)
        )
        & (wave_energy >= 195)
        & (wave_direction not in unwanted_wave_directions)
        & (wave_direction_predominant not in unwanted_wave_directions)
    ):
        return True
    return False


def punta_mujeres_low_wind_conditions(
    wave_direction_predominant: str,
    wave_direction: str,
    wave_energy: int,
):
    punta_mujeres_wave_directions = ["N", "NE", "E", "NNW", "NNE", "NW"]
    unwanted_wave_directions = ["WNW"]
    if (
        (
            (wave_direction_predominant in punta_mujeres_wave_directions)
            | (wave_direction in punta_mujeres_wave_directions)
        )
        & (wave_energy >= 195)
        & (wave_direction not in unwanted_wave_directions)
        & (wave_direction_predominant not in unwanted_wave_directions)
    ):
        return True
    return False


def papagayo_conditions(
    wind_direction_predominant: str,
    wave_direction_predominant: str,
    wind_direction: str,
    wave_direction: str,
    wave_energy: int,
    tide_percentage: float,
):
    papagayo_wave_directions = [
        "W",
        "WNW",
    ]

    if (
        (
            papagayo_favorable_wind(wind_direction_predominant, wind_direction)
            & (wave_direction_predominant in papagayo_wave_directions)
            | (wave_direction in papagayo_wave_directions)
        )
        & (wave_energy >= 138)
        & (tide_percentage <= 50)
    ):
        return True
    return False


def papagayo_low_wind_conditions(
    wave_direction_predominant: str,
    wave_direction: str,
    wave_energy: int,
    tide_percentage: float,
):
    papagayo_wave_directions = [
        "W",
        "WNW",
    ]

    if (
        (
            (wave_direction_predominant in papagayo_wave_directions)
            | (wave_direction in papagayo_wave_directions)
        )
        & (wave_energy >= 138)
        & (tide_percentage <= 50)
    ):
        return True
    return False


def west_swell_high_tide_conditions(
    wind_direction_predominant: str,
    wave_direction_predominant: str,
    wind_direction: str,
    wave_direction: str,
    wave_energy: int,
    tide_percentage: float,
):
    papagayo_wave_directions = [
        "W",
        "WNW",
    ]

    if (
        (
            papagayo_favorable_wind(wind_direction_predominant, wind_direction)
            & (wave_direction_predominant in papagayo_wave_directions)
            | (wave_direction in papagayo_wave_directions)
        )
        & (wave_energy >= 138)
        & (tide_percentage > 50)
    ):
        return True
    return False


def west_swell_high_tide_low_wind_conditions(
    wave_direction_predominant: str,
    wave_direction: str,
    wave_energy: int,
    tide_percentage: float,
):
    papagayo_wave_directions = [
        "W",
        "WNW",
    ]

    if (
        (
            (wave_direction_predominant in papagayo_wave_directions)
            | (wave_direction in papagayo_wave_directions)
        )
        & (wave_energy >= 138)
        & (tide_percentage > 50)
    ):
        return True
    return False


def papelillo_conditions(
    wind_direction_predominant: str,
    wave_direction_predominant: str,
    wind_direction: str,
    wave_direction: str,
    tide_percentage: float,
):
    papelillo_wave_directions = [
        "N",
        "NW",
        "NE",
    ]
    unwanted_wave_directions = ["WNW"]

    if (
        (
            papelillo_favorable_wind(wind_direction_predominant, wind_direction)
            & (
                (wave_direction_predominant in papelillo_wave_directions)
                | (wave_direction in papelillo_wave_directions)
            )
        )
        & (wave_direction not in unwanted_wave_directions)
        & (tide_percentage <= 50)
    ):
        return True
    return False


def papelillo_low_wind_conditions(
    wave_direction_predominant: str,
    wave_direction: str,
    tide_percentage: float,
):
    papelillo_wave_directions = [
        "N",
        "NW",
        "NE",
    ]
    unwanted_wave_directions = ["WNW"]
    if (
        (
            (wave_direction_predominant in papelillo_wave_directions)
            | (wave_direction in papelillo_wave_directions)
        )
        & (wave_direction not in unwanted_wave_directions)
        & (tide_percentage <= 50)
    ):
        return True
    return False


def caleta_caballo_conditions(
    wind_direction_predominant: str,
    wave_direction_predominant: str,
    wind_direction: str,
    wave_direction: str,
):
    caleta_caballo_wave_directions = ["N", "NW", "NE"]
    unwanted_wave_directions = ["WNW"]

    if (
        caleta_caballo_favorable_wind(wind_direction_predominant, wind_direction)
        & (
            (wave_direction_predominant in caleta_caballo_wave_directions)
            | (wave_direction in caleta_caballo_wave_directions)
        )
        & (wave_direction not in unwanted_wave_directions)
    ):
        return True
    return False


def caleta_caballo_low_wind_conditions(
    wave_direction_predominant: str,
    wave_direction: str,
):
    caleta_caballo_wave_directions = ["N", "NW", "NE"]
    unwanted_wave_directions = ["WNW"]
    if (
        (wave_direction_predominant in caleta_caballo_wave_directions)
        | (wave_direction in caleta_caballo_wave_directions)
    ) & (wave_direction not in unwanted_wave_directions):
        return True
    return False


def bastian_conditions(
    wind_direction_predominant: str,
    wave_direction_predominant: str,
    wind_direction: str,
    wave_direction: str,
    wind_speed: float,
    tide_percentage: float,
):
    bastian_wind_directions = ["NE", "N"]
    bastian_wave_directions = ["N", "NW", "NE", "E", "S"]

    if (
        (
            (
                (wind_direction_predominant in bastian_wind_directions)
                | (wind_direction in bastian_wind_directions)
            )
            & (wave_direction_predominant in bastian_wave_directions)
            | (wave_direction in bastian_wave_directions)
        )
        & (wind_speed >= 19.0)
        & (tide_percentage >= 50)
    ):
        return True
    return False


def barcarola_conditions(
    wind_direction_predominant: str,
    wave_direction_predominant: str,
    wind_direction: str,
    wave_direction: str,
    wind_speed: float,
    wave_height: float,
    tide_percentage: float,
):
    barcarola_wind_directions = ["NE", "N"]
    barcarola_wave_directions = ["N", "NW", "NE", "E", "S"]

    if (
        (
            (
                (wind_direction_predominant in barcarola_wind_directions)
                | (wind_direction in barcarola_wind_directions)
            )
            & (wave_direction_predominant in barcarola_wave_directions)
            | (wave_direction in barcarola_wave_directions)
        )
        & (wind_speed >= 19.0)
        & (wave_height >= 1.7)  # TODO Jugar con esto
        & (tide_percentage <= 50)
    ):
        return True
    return False


def lasanta_conditions(
    wind_direction_predominant: str,
    wave_direction_predominant: str,
    wind_direction: str,
    wave_direction: str,
    wave_height: float,
    wave_period: int,
):
    lasanta_wave_directions = ["N", "NW", "NE"]
    unwanted_wave_directions = ["WNW"]

    if (
        (
            lasanta_favorable_wind(wind_direction_predominant, wind_direction)
            & (
                (wave_direction_predominant in lasanta_wave_directions)
                | (wave_direction in lasanta_wave_directions)
            )
        )
        & (wave_direction not in unwanted_wave_directions)
        & (wave_height >= 1)
        & (wave_period >= 7)
    ):
        return True
    return False


def famara_conditions(
    wind_direction_predominant: str,
    wave_direction_predominant: str,
    wind_direction: str,
    wave_direction: str,
    wave_height: float,
    wave_period: int,
):
    famara_wave_directions = ["N", "NW", "NE"]
    unwanted_wave_directions = ["WNW"]
    if (
        (
            famara_favorable_wind(wind_direction_predominant, wind_direction)
            & (
                (wave_direction_predominant in famara_wave_directions)
                | (wave_direction in famara_wave_directions)
            )
            & (wave_direction not in unwanted_wave_directions)
        )
        & (wave_height >= 1)
        & (wave_period >= 7)
    ):
        return True
    return False


def lasanta_low_wind_conditions(
    wave_direction_predominant: str,
    wave_direction: str,
    wave_height: float,
    wave_period: int,
):
    lasanta_wave_directions = ["N", "NW", "NE"]
    unwanted_wave_directions = ["WNW"]
    if (
        (
            (wave_direction_predominant in lasanta_wave_directions)
            | (wave_direction in lasanta_wave_directions)
        )
        & (wave_direction not in unwanted_wave_directions)
        & (wave_height >= 1)
        & (wave_period >= 7)
    ):
        return True
    return False


def famara_low_wind_conditions(
    wave_direction_predominant: str,
    wave_direction: str,
    wave_height: float,
    wave_period: int,
):
    famara_wave_directions = ["N", "NW", "NE"]
    unwanted_wave_directions = ["WNW"]
    if (
        (
            (wave_direction_predominant in famara_wave_directions)
            | (wave_direction in famara_wave_directions)
        )
        & (wave_direction not in unwanted_wave_directions)
        & (wave_height >= 1)
        & (wave_period >= 7)
    ):
        return True
    return False


def big_waves_conditions(
    wave_height: float, wave_direction: str, wave_direction_predominant: str
):
    big_wave_directions = ["N", "NE", "E"]
    unwanted_wave_directions = ["WNW"]
    if (
        (
            (wave_direction_predominant in big_wave_directions)
            | (wave_direction in big_wave_directions)
        )
        & (wave_direction not in unwanted_wave_directions)
        & (wave_height > 2.5)  # Si en 2.5 no hay nada, revisar en 3
    ):
        return True
    return False


def famara_favorable_wind(wind_direction_predominant, wind_direction):
    famara_wind_directions = ["S"]
    return is_favorable_wind(
        wind_direction_predominant, wind_direction, famara_wind_directions
    )


def east_favorable_wind(wind_direction_predominant, wind_direction):
    east_wind_directions = ["E", "NE", "SE"]
    return is_favorable_wind(
        wind_direction_predominant, wind_direction, east_wind_directions
    )


def lasanta_favorable_wind(wind_direction_predominant, wind_direction):
    return east_favorable_wind(wind_direction_predominant, wind_direction)


def papagayo_favorable_wind(wind_direction_predominant, wind_direction):
    return east_favorable_wind(wind_direction_predominant, wind_direction)


def papelillo_favorable_wind(wind_direction_predominant, wind_direction):
    east_wind_directions = ["E", "SE"]
    return is_favorable_wind(
        wind_direction_predominant, wind_direction, east_wind_directions
    )


def punta_mujeres_favorable_wind(wind_direction_predominant, wind_direction):
    punta_mujeres_wind_directions = ["N", "NW"]
    return is_favorable_wind(
        wind_direction_predominant, wind_direction, punta_mujeres_wind_directions
    )


def caleta_caballo_favorable_wind(wind_direction_predominant, wind_direction):
    caleta_caballo_wind_directions = ["W", "SW", "WNW"]
    return is_favorable_wind(
        wind_direction_predominant, wind_direction, caleta_caballo_wind_directions
    )


def is_favorable_wind(
    wind_direction_predominant: str, wind_direction: str, target_wind_directions: str
):
    if (wind_direction_predominant in target_wind_directions) | (
        wind_direction in target_wind_directions
    ):
        return True
    return False


def get_low_wind_spot(
    wind_direction_predominant,
    wind_direction,
    wave_direction_predominant,
    wave_direction,
    wave_height,
    wave_period,
    wave_energy,
    tide_percentage,
):
    if famara_low_wind_conditions(
        wave_direction_predominant,
        wave_direction,
        wave_height,
        wave_period,
    ) and famara_favorable_wind(wind_direction_predominant, wind_direction):
        return "Famara"
    elif papelillo_low_wind_conditions(
        wave_direction_predominant,
        wave_direction,
        tide_percentage,
    ) and papelillo_favorable_wind(wind_direction_predominant, wind_direction):
        return "Papelillo"
    elif lasanta_low_wind_conditions(
        wave_direction_predominant,
        wave_direction,
        wave_height,
        wave_period,
    ) and lasanta_favorable_wind(wind_direction_predominant, wind_direction):
        return "La Santa"
    elif punta_mujeres_low_wind_conditions(
        wave_direction_predominant, wave_direction, wave_energy
    ) and punta_mujeres_favorable_wind(wind_direction_predominant, wind_direction):
        return "Punta Mujeres"
    elif caleta_caballo_low_wind_conditions(
        wave_direction_predominant,
        wave_direction,
    ) and caleta_caballo_favorable_wind(wind_direction_predominant, wind_direction):
        return "Caleta Caballo"
    elif papagayo_low_wind_conditions(
        wave_direction_predominant,
        wave_direction,
        wave_energy,
        tide_percentage,
    ) and papagayo_favorable_wind(wind_direction_predominant, wind_direction):
        return "Papagayo-Tiburón (Fuerza oeste - vacía)"
    elif west_swell_high_tide_low_wind_conditions(
        wave_direction_predominant,
        wave_direction,
        wave_energy,
        tide_percentage,
    ):
        return "Fuerza oeste - llena"
    elif caleta_caballo_low_wind_conditions(
        wave_direction_predominant,
        wave_direction,
    ):
        return "Caleta Caballo"
    elif papagayo_low_wind_conditions(
        wave_direction_predominant,
        wave_direction,
        wave_energy,
        tide_percentage,
    ):
        return "Papagayo-Tiburón (Fuerza oeste - vacía)"
    elif punta_mujeres_low_wind_conditions(
        wave_direction_predominant,
        wave_direction,
        wave_energy,
    ):
        return "Punta Mujeres"
    elif lasanta_low_wind_conditions(
        wave_direction_predominant,
        wave_direction,
        wave_height,
        wave_period,
    ):
        return "La Santa"

    elif famara_low_wind_conditions(
        wave_direction_predominant,
        wave_direction,
        wave_height,
        wave_period,
    ):
        return "Famara"
    else:
        return "No Clasificado"


def is_low_wind(wind_speed: float) -> bool:
    return wind_speed < 10.0


def generate_spot_names(forecast: Dict[str, list]) -> list:
    spot_names = []
    wind_direction_predominant = forecast["wind_direction_predominant"]
    wave_direction_predominant = forecast["wave_direction_predominant"]
    wind_direction = forecast["wind_direction"]
    wave_direction = forecast["wave_direction"]
    wind_speed = forecast["wind_speed"]
    wave_period = forecast["wave_period"]
    wave_height = forecast["wave_height"]
    tide_percentage = forecast["tide_percentage"]
    energy = forecast["energy"]

    for wid_predominant, wad_predominant, wid, wad, ws, tp, wp, wh, e in zip(
        wind_direction_predominant,
        wave_direction_predominant,
        wind_direction,
        wave_direction,
        wind_speed,
        tide_percentage,
        wave_period,
        wave_height,
        energy,
    ):
        if is_low_wind(wind_speed=ws):
            spot = get_low_wind_spot(
                wind_direction_predominant=wid_predominant,
                wind_direction=wid,
                wave_direction_predominant=wad_predominant,
                wave_direction=wad,
                wave_height=wh,
                wave_period=wp,
                wave_energy=e,
                tide_percentage=tp,
            )
            spot_names.append(spot)
        elif big_waves_conditions(
            wave_height=wh,
            wave_direction=wad,
            wave_direction_predominant=wad_predominant,
        ):
            spot_names.append("Olas grandes > 2.5m, revisar costa de playa honda")
        elif punta_mujeres_conditions(
            wind_direction_predominant=wid_predominant,
            wave_direction_predominant=wad_predominant,
            wind_direction=wid,
            wave_direction=wad,
            wave_energy=e,
        ):
            spot_names.append("Punta Mujeres")
        elif papagayo_conditions(
            wind_direction_predominant=wid_predominant,
            wave_direction_predominant=wad_predominant,
            wind_direction=wid,
            wave_direction=wad,
            wave_energy=e,
            tide_percentage=tp,
        ):
            spot_names.append("Papagayo-Tiburón (Fuerza oeste - vacía)")
        elif west_swell_high_tide_conditions(
            wind_direction_predominant=wid_predominant,
            wave_direction_predominant=wad_predominant,
            wind_direction=wid,
            wave_direction=wad,
            wave_energy=e,
            tide_percentage=tp,
        ):
            spot_names.append("Fuerza oeste - llena")
        elif papelillo_conditions(
            wind_direction_predominant=wid_predominant,
            wave_direction_predominant=wad_predominant,
            wind_direction=wid,
            wave_direction=wad,
            tide_percentage=tp,
        ):
            spot_names.append("Papelillo")
        elif caleta_caballo_conditions(
            wind_direction_predominant=wid_predominant,
            wave_direction_predominant=wad_predominant,
            wind_direction=wid,
            wave_direction=wad,
        ):
            spot_names.append("Caleta Caballo")
        elif barcarola_conditions(
            wind_direction_predominant=wid_predominant,
            wave_direction_predominant=wad_predominant,
            wind_direction=wid,
            wave_direction=wad,
            wind_speed=ws,
            wave_height=wh,
            tide_percentage=tp,
        ):
            spot_names.append("Barcarola")
        elif bastian_conditions(
            wind_direction_predominant=wid_predominant,
            wave_direction_predominant=wad_predominant,
            wind_direction=wid,
            wave_direction=wad,
            wind_speed=ws,
            tide_percentage=tp,
        ):
            spot_names.append("Bastián")
        elif famara_conditions(
            wind_direction_predominant=wid_predominant,
            wave_direction_predominant=wad_predominant,
            wind_direction=wid,
            wave_direction=wad,
            wave_height=wh,
            wave_period=wp,
        ):
            spot_names.append("Famara")
        elif lasanta_conditions(
            wind_direction_predominant=wid_predominant,
            wave_direction_predominant=wad_predominant,
            wind_direction=wid,
            wave_direction=wad,
            wave_height=wh,
            wave_period=wp,
        ):
            spot_names.append("La Santa")
        else:
            spot_names.append("No Clasificado")
    return spot_names


# margen de 20 grados en N,S,E,O
def angle_to_direction(angle):
    angle %= 360
    if 0 <= angle < 10 or angle >= 350:
        return "North"
    elif 10 <= angle < 80:
        return "NorthEast"
    elif 80 <= angle < 100:
        return "East"
    elif 100 <= angle < 170:
        return "SouthEast"
    elif 170 <= angle < 190:
        return "South"
    elif 190 <= angle < 260:
        return "SouthWest"
    elif 260 <= angle < 280:
        return "West"
    elif 280 <= angle < 350:
        return "NorthWest"


def export_to_html(filename, response: Response):
    soup = BeautifulSoup(response.text, "html.parser")
    with open(filename, "w") as file:
        file.write(soup.prettify())


def import_html(filename):
    with open(filename, "r") as file:
        return file.read()


def combine_df(df1, df2):
    df = pl.concat([df1, df2])
    return df


def convert_datestr_format(datestr):
    day = int(datestr.split(" ")[-1].strip())
    month_name = datestr.split(" ")[-2].strip()
    month = MONTH_MAPPING[month_name]
    current_year = datetime.now().year

    date_obj = datetime(current_year, int(month), day)

    return date_obj.strftime("%d/%m/%Y")


def open_browser():
    my_user_agent = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    )

    options = webdriver.ChromeOptions()
    options.add_argument("--lang=es")
    options.add_argument("--headless")
    options.add_argument(f"--user-agent={my_user_agent}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    options.page_load_strategy = "eager"
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)

    browser = webdriver.Chrome(options=options)
    return browser


def render_html(url, tag_to_wait=None, timeout=10):
    try:
        browser = open_browser()
        browser.get(url)
        if tag_to_wait:
            element = WebDriverWait(browser, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, tag_to_wait))
            )
            assert element
        html_content = browser.page_source
        return html_content
    except Exception as e:
        raise e
    finally:
        browser.close()
        browser.quit()


def rename_key(dictionary, old_key, new_key):
    if old_key in dictionary:
        dictionary[new_key] = dictionary.pop(old_key)

    return dictionary


def create_date_name_column(dates: list) -> list:
    date_names = []
    today_dt = datetime.now().date()
    tomorrow_dt = today_dt + timedelta(days=1)
    day_after_tomorrow_dt = today_dt + timedelta(days=2)
    yesterday_dt = today_dt - timedelta(days=1)
    for date in dates:
        if date.date() == today_dt:
            date_names.append("Hoy")
        elif date.date() == tomorrow_dt:
            date_names.append("Mañana")
        elif date.date() == day_after_tomorrow_dt:
            date_names.append("Pasado")
        elif date.date() == yesterday_dt:
            date_names.append("Ayer")
        else:
            date_names.append("Otro día")
    return date_names


def create_wind_description_column(df: pl.DataFrame) -> pl.DataFrame:
    df = df.with_columns(
        pl.col("wind_speed").apply(classify_wind_speed).alias("wind_description")
    )

    return df


def get_day_name(days_to_add: float) -> str:
    today = date.today()
    day = today + timedelta(days=days_to_add)
    day_name_number = day.strftime("%m-%d, %A")

    return day_name_number


def create_direction_predominant_column(directions: list) -> list:
    return [get_predominant_direction(int(dir)) for dir in directions]


def final_forecast_format(df: pl.DataFrame):
    if not df.is_empty():
        df.sort(by=["date", "time", "spot_name"], descending=[True, True, True])
        df = df.with_columns(
            pl.col("time")
            .str.strptime(pl.Time, format="%H:%M", strict=False)
            .alias("parsed time")
        )
        datetimes = df["parsed time"]
        _6_AM = time(hour=6, minute=0, second=0, microsecond=0)
        _19_PM = time(hour=19, minute=0, second=0, microsecond=0)
        mask = (datetimes >= _6_AM) & (datetimes <= _19_PM)
        df = df.filter(mask)

        common_columns = [
            "date_name",
            "date",
            "time",
            "energy",
            "wind_speed",
            "tide_percentage",
            "nearest_tide",
            "tide",
            "datetime",
            "spot_name",
            "wind_direction_predominant",
            "wave_direction_predominant",
            "wave_height",
            "wave_period",
            "wind_direction",
            "wave_direction",
            "wind_direction_degrees",
            "wave_direction_degrees",
        ]
        df = df[common_columns]
    return df


def degrees_to_direction(degrees):
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    index = round(degrees / 45) % 8
    return directions[index]


def classify_wind_speed(speed_knots):
    if speed_knots < 1:
        return "Calma"
    elif speed_knots <= 3:
        return "Brisita suave"
    elif speed_knots <= 6:
        return "Brisa my débil"
    elif speed_knots <= 10:
        return "Brisa ligera"
    elif speed_knots <= 16:
        return "Brisa moderada"
    elif speed_knots <= 21:
        return "Brisa casi fuerte"
    elif speed_knots <= 27:
        return "Brisa fuerte"
    elif speed_knots <= 33:
        return "Viento fuerte"
    elif speed_knots <= 40:
        return "Viento duro"
    elif speed_knots <= 47:
        return "Viento muy duro"
    elif speed_knots <= 55:
        return "Temporal"
    elif speed_knots <= 63:
        return "Borrasca"
    else:
        return "Huracán"


def feet_to_meters(feet):
    meters = feet * 0.3048
    return meters


def datetime_to_frontend_str(dt: datetime) -> str:
    return dt.strftime(FRONT_END_DATE_FORMAT).capitalize()


def construct_date_selection_list(
    min_value: datetime, max_value: datetime, scraped_datetime_list: list
) -> list:
    date_selection = []
    for scraped_datetime in scraped_datetime_list:
        if scraped_datetime >= min_value and scraped_datetime <= max_value:
            date_selection.append(datetime_to_frontend_str(scraped_datetime))
    return date_selection


def datetime_to_str(dt: datetime, dt_format: str) -> str:
    return dt.strftime(dt_format)


def timestamp_to_datetime(timestamp_date: int) -> datetime:
    return datetime.utcfromtimestamp(timestamp_date)


def add_offset_to_datetime(dt: datetime, utc_offset: int) -> datetime:
    return dt + timedelta(hours=utc_offset)


def timestamp_to_datetimestr(timestamp_date: int, utc_offset: int) -> str:
    datetime_dt = timestamp_to_datetime(timestamp_date)
    datestr = datetime_to_str(
        add_offset_to_datetime(datetime_dt, utc_offset), INTERNAL_DATE_STR_FORMAT
    )
    timestr = datetime_to_str(
        add_offset_to_datetime(datetime_dt, utc_offset), INTERNAL_TIME_STR_FORMAT
    )
    return datestr, timestr


def datestr_to_datetime(dtstr, format) -> datetime:
    return datetime.strptime(dtstr, format)


def get_datename(dt: str):
    dt_dt = datestr_to_datetime(dt, INTERNAL_DATE_STR_FORMAT).date()

    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    day_after_tomorrow = today + timedelta(days=2)

    if dt_dt == today:
        return "Today"
    elif dt_dt == tomorrow:
        return "Tomorrow"
    elif dt_dt == day_after_tomorrow:
        return "Day After Tomorrow"
    else:
        return "Another Day"


def kmh_to_knots(kmh):
    return kmh / 1.852


def mps_to_knots(mps):
    return mps * 1.94384


def convert_all_values_of_dict_to_min_length(data):
    min_len = obtain_minimum_len_of_dict_values(data)
    new_data = {}
    for key, value in data.items():
        new_data[key] = value[:min_len]
    return new_data


def obtain_minimum_len_of_dict_values(data: dict):
    data_value_lens = []
    for _, value in data.items():
        data_value_lens.append(len(value))
    return min(data_value_lens)


def generate_dates(times: list) -> list:
    dates = []
    date = datetime.now().date()
    for index, time in enumerate(times):
        if (
            index - 1 >= 0
            and datestr_to_datetime(time, "%H:%M").time()
            < datestr_to_datetime(times[index - 1], "%H:%M").time()
        ):
            date += timedelta(days=1)
        date_str = datetime.strftime(date, "%d/%m/%Y")
        dates.append(date_str)
    return dates


def are_contraries(dir1, dir2):
    return CONTRARIES.get(dir1) == dir2


def get_maximum_len_str(wind_direction, wave_direction):
    if len(wind_direction) > len(wave_direction):
        return wind_direction
    else:
        return wave_direction


def get_minimum_len_str(wind_direction, wave_direction):
    if len(wind_direction) > len(wave_direction):
        return wave_direction
    else:
        return wind_direction


def count_contraries(wind_direction, wave_direction):
    counter = 0
    if len(wind_direction) == len(wave_direction):
        for i in range(len(wind_direction)):
            if are_contraries(wind_direction[i], wave_direction[i]):
                counter += 1
    else:
        max_len_str = get_maximum_len_str(wind_direction, wave_direction)
        min_len_str = get_minimum_len_str(wind_direction, wave_direction)
        for mili in min_len_str:
            for mali in max_len_str:
                if are_contraries(mili, mali):
                    counter += 1
                if counter >= len(min_len_str):
                    break
    return counter


def get_wind_status(wind_direction, wave_direction):
    wd_len = len(wind_direction)
    wv_len = len(wave_direction)
    len_contraries = count_contraries(wind_direction, wave_direction)
    if wd_len == wv_len and wd_len == len_contraries:
        return "Offshore"
    elif len_contraries >= 1:
        return "Cross-off"
    return "Onshore"


def generate_tides(tide_data: list, forecast_datetimes: list) -> list:
    tide_status_list = []
    tides_datetimes_list = [item["datetime"] for item in tide_data]
    tides_tide_list = [item["tide"] for item in tide_data]

    for forecast_datetime in forecast_datetimes:
        closest_datetime = min(
            tides_datetimes_list, key=lambda dt: abs(dt - forecast_datetime)
        )
        closest_datetime_index = tides_datetimes_list.index(closest_datetime)
        tide_status = tides_tide_list[closest_datetime_index]

        try:
            next_tide_datetime = tides_datetimes_list[closest_datetime_index + 1]
        except IndexError:
            # Marea alta y baja hay 6h y 12.5 min
            next_tide_datetime = closest_datetime + timedelta(hours=6, minutes=12.5)

        tide_hour = closest_datetime.time()
        next_tide_hour = next_tide_datetime.time()

        if forecast_datetime > closest_datetime:
            status = "Bajando" if tide_status == "pleamar" else "Subiendo"
            s = f"{status} hasta las {next_tide_hour.strftime('%H:%M')}"
        elif forecast_datetime < closest_datetime:
            status = "Subiendo" if tide_status == "pleamar" else "Bajando"
            s = f"{status} hasta las {tide_hour.strftime('%H:%M')}"
        else:
            s = f"{tide_status} del todo a las {tide_hour.strftime('%H:%M')}"

        tide_status_list.append(s)

    return tide_status_list


def generate_nearest_tides(tide_data: dict, forecast_datetimes: dict) -> list:
    nearest_tides = []
    tides_datetimes_list = [item["datetime"] for item in tide_data]
    tides_tide_list = [item["tide"] for item in tide_data]

    for forecast_datetime in forecast_datetimes:
        closest_datetime = min(
            tides_datetimes_list, key=lambda dt: abs(dt - forecast_datetime)
        )
        closest_datetime_index = tides_datetimes_list.index(closest_datetime)
        tide_status = tides_tide_list[closest_datetime_index]
        tide_status = "Llena" if tide_status == "pleamar" else "Vacía"
        nearest_tides.append(tide_status)
    return nearest_tides


def generate_tide_percentages(tide_data: dict, forecast_datetimes: list) -> list:
    tide_percentages = []
    tides_datetimes_list = [item["datetime"] for item in tide_data]
    tides_tide_list = [item["tide"] for item in tide_data]

    for forecast_datetime in forecast_datetimes:
        sorted_datetimes = sorted(
            tides_datetimes_list, key=lambda dt: abs(dt - forecast_datetime)
        )
        closest_datetime_1 = sorted_datetimes[0]
        closest_datetime_2 = sorted_datetimes[1]

        closest_datetime_index_1 = tides_datetimes_list.index(closest_datetime_1)

        if tides_tide_list[closest_datetime_index_1] == "pleamar":
            high_tide_hour = closest_datetime_1
            low_tide_hour = closest_datetime_2
        else:
            high_tide_hour = closest_datetime_2
            low_tide_hour = closest_datetime_1

        tide_percentage = calculate_tide_percentage(
            high_tide_hour, forecast_datetime, low_tide_hour
        )
        tide_percentages.append(tide_percentage)

    return tide_percentages


def find_next_tide(tides_datetimes_list, tides_tide_list, start_index, tide_type):
    for i in range(start_index + 1, len(tides_datetimes_list)):
        if tides_tide_list[i].lower() == tide_type:
            return tides_datetimes_list[i]
    raise ValueError(f"No {tide_type} found after index {start_index}")


from datetime import datetime, timedelta


def calculate_tide_percentage(
    high_tide_hour: datetime, current_hour: datetime, low_tide_hour: datetime
) -> float:
    if high_tide_hour > low_tide_hour:
        total_cycle_duration = (high_tide_hour - low_tide_hour).total_seconds()
    else:
        total_cycle_duration = (low_tide_hour - high_tide_hour).total_seconds()

    if current_hour < high_tide_hour:
        deviation = (high_tide_hour - current_hour).total_seconds()
        percentage = (deviation / total_cycle_duration) * 100
    elif current_hour > low_tide_hour:
        deviation = (current_hour - low_tide_hour).total_seconds()
        percentage = 100 - (deviation / total_cycle_duration) * 100
    else:
        deviation = (current_hour - high_tide_hour).total_seconds()
        percentage = (deviation / total_cycle_duration) * 100

    percentage = max(0, min(100, percentage))
    calculed_percentage = math.ceil(percentage)
    returned_percentage = 100 - calculed_percentage
    return returned_percentage


def generate_datetimes(dates, times):
    datetimes = []
    for date, time in zip(dates, times):
        year = datetime.strptime(date, FRONT_END_DATE_FORMAT).year
        month = datetime.strptime(date, FRONT_END_DATE_FORMAT).month
        day = datetime.strptime(date, FRONT_END_DATE_FORMAT).day
        hour = int(time.split(":")[0])
        minute = int(time.split(":")[1])
        datetimes.append(datetime(year, month, day, hour, minute))
    return datetimes


def datestr_to_frontend_format(input_text):
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

    return datetime_to_frontend_str(date_datetime)


def filter_dataframe(
    entry_df: pl.DataFrame, spot_conditions: dict, three_near_days: bool
) -> pl.DataFrame:
    column_names = list(entry_df.columns)
    spot_name_list = []
    wave_direction_list = []
    wind_direction_list = []
    spot_names = spot_conditions["spot_name"]
    # TODO refactorizar esto
    for spot in spot_names:
        filtered_df = entry_df.filter(pl.col("spot_name").str.contains(spot))
        spot_name_list.append(filtered_df)

    result_list = [df for df in spot_name_list if not df.is_empty()]
    if len(result_list) > 0:
        result_df = result_list[0]
    else:
        return pl.DataFrame()

    if "wave_direction" in spot_conditions and "wave_direction" in column_names:
        directions = spot_conditions["wave_direction"]
        for direction in directions:
            filtered_df = result_df.filter(
                pl.col("wave_direction").str.contains(direction)
            )
            wave_direction_list.append(filtered_df)

        result_list = [df for df in wave_direction_list if not df.is_empty()]
        if len(result_list) > 0:
            result_df = result_list[0]
        else:
            return pl.DataFrame()

    if "wave_period" in spot_conditions and "wave_period" in column_names:
        result_df = result_df.filter(
            pl.col("wave_period") >= spot_conditions["wave_period"]
        )
    if "wave_height" in spot_conditions and "wave_height" in column_names:
        result_df = result_df.filter(
            pl.col("wave_height") >= spot_conditions["wave_height"]
        )
    if "energy" in spot_conditions and "energy" in column_names:
        result_df = result_df.filter(pl.col("energy") >= spot_conditions["energy"])

    if "wind_direction" in spot_conditions and "wind_direction" in column_names:
        directions = spot_conditions["wind_direction"]
        for direction in directions:
            filtered_df = result_df.filter(
                pl.col("wind_direction").str.contains(direction)
            )
            wind_direction_list.append(filtered_df)

        result_list = [df for df in wind_direction_list if not df.is_empty()]
        if len(result_list) > 0:
            result_df = result_list[0]
        else:
            return pl.DataFrame()

    if three_near_days:
        date_names = ["Hoy", "Mañana", "Pasado"]
        result_df = result_df.filter(pl.col("date_name").is_in(date_names))
    return result_df


def read_json(json_name: str) -> dict:
    with open(json_name) as f:
        return json.load(f)


def filter_spot_dataframe(
    spot_name: str, df: pl.DataFrame, three_near_days: bool
) -> pl.DataFrame:
    file = f"./assets/conditions.json"
    conditions_data = read_json(file)
    return filter_dataframe(df, conditions_data[spot_name], three_near_days)


def get_predominant_direction(direction: float) -> str:
    if direction == 0 or direction == 360:
        return "N"
    elif direction == 90:
        return "E"
    elif direction == 180:
        return "S"
    elif direction == 270:
        return "W"
    elif direction > 0 and direction < 90:
        return "NE"
    elif direction > 90 and direction < 180:
        return "SE"
    elif direction > 180 and direction < 270:
        return "SW"
    elif direction > 270 and direction < 360:
        return "NW"
