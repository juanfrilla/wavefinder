import math
import polars as pl
from datetime import datetime, date, time, timedelta, timezone
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


def calculate_energy(wave_height, wave_period, width=1.0, water_density=1025):
    g = 9.81
    wavelength = (g * wave_period**2) / (2 * 3.14159)
    energy_density = (1 / 8) * water_density * g * wave_height**2
    energy_joules = energy_density * wavelength * width
    energy_kj = energy_joules / 1000

    return math.ceil(energy_kj)


def generate_energy(wave_heights: list, wave_periods: list):
    return [
        calculate_energy(wave_height=wave_height, wave_period=wave_period)
        for wave_height, wave_period in zip(wave_heights, wave_periods)
    ]


def punta_mujeres_conditions(
    wind_direction_predominant: str,
    wave_direction_predominant: str,
    wind_direction: str,
    wave_direction: str,
    wave_energy: int,
):
    return punta_mujeres_favorable_wind(wind_direction_predominant, wind_direction) & (
        punta_mujeres_low_wind_conditions(
            wave_direction_predominant, wave_direction, wave_energy
        )
    )


def punta_mujeres_low_wind_conditions(
    wave_direction_predominant: str,
    wave_direction: str,
    wave_energy: int,
):
    punta_mujeres_wave_directions = ["N", "NE", "E", "NNW", "NNE", "NW"]
    unwanted_wave_directions = ["WNW"]
    return (
        (
            (wave_direction_predominant in punta_mujeres_wave_directions)
            | (wave_direction in punta_mujeres_wave_directions)
        )
        & (wave_energy >= 1000)
        & (wave_direction not in unwanted_wave_directions)
        & (wave_direction_predominant not in unwanted_wave_directions)
    )


def papagayo_conditions(
    wind_direction_predominant: str,
    wave_direction_predominant: str,
    wind_direction: str,
    wave_direction: str,
    wave_energy: int,
    tide_percentage: float,
):
    return papagayo_favorable_wind(wind_direction_predominant, wind_direction) & (
        papagayo_low_wind_conditions(
            wave_direction_predominant, wave_direction, wave_energy, tide_percentage
        )
    )


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

    return (
        (
            (wave_direction_predominant in papagayo_wave_directions)
            | (wave_direction in papagayo_wave_directions)
        )
        & (wave_energy >= 1200)
        & (tide_percentage <= 50)
    )


def tiburon_conditions(
    wind_direction_predominant: str,
    wave_direction_predominant: str,
    wind_direction: str,
    wave_direction: str,
    wave_energy: int,
):
    return tiburon_favorable_wind(wind_direction_predominant, wind_direction) & (
        tiburon_low_wind_conditions(
            wave_direction_predominant, wave_direction, wave_energy
        )
    )


def tiburon_low_wind_conditions(
    wave_direction_predominant: str,
    wave_direction: str,
    wave_energy: int,
):
    papagayo_wave_directions = [
        "W",
        "WNW",
    ]

    return (
        (wave_direction_predominant in papagayo_wave_directions)
        | (wave_direction in papagayo_wave_directions)
    ) & (wave_energy >= 5000)


def bajorisco_conditions(
    wind_direction_predominant: str,
    wave_direction_predominant: str,
    wind_direction: str,
    wave_direction: str,
    wave_energy: int,
    tide_percentage: float,
):

    return bajorisco_favorable_wind(
        wind_direction_predominant, wind_direction
    ) & west_swell_high_tide_low_wind_conditions(
        wave_direction_predominant, wave_direction, wave_energy, tide_percentage
    )


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

    return (
        (
            (wave_direction_predominant in papagayo_wave_directions)
            | (wave_direction in papagayo_wave_directions)
        )
        & (wave_energy >= 900)
        & (tide_percentage > 50)
    )


def west_swell_low_tide_low_wind_conditions(
    wave_direction_predominant: str,
    wave_direction: str,
    wave_energy: int,
    tide_percentage: float,
):
    papagayo_wave_directions = [
        "W",
        "WNW",
    ]

    return (
        (
            (wave_direction_predominant in papagayo_wave_directions)
            | (wave_direction in papagayo_wave_directions)
        )
        & (wave_energy >= 900)
        & (tide_percentage < 50)
    )


def papelillo_conditions(
    wave_direction_predominant: str,
    wave_direction: str,
    wave_energy: int,
    wind_direction_predominant: str,
    wind_direction: str,
):
    return papelillo_low_wind_conditions(
        wave_direction_predominant, wave_direction, wave_energy
    ) and papelillo_favorable_low_wind(
        wind_direction_predominant=wind_direction_predominant,
        wind_direction=wind_direction,
    )


def papelillo_low_wind_conditions(
    wave_direction_predominant: str,
    wave_direction: str,
    wave_energy: int,
):
    papelillo_wave_directions = [
        "N",
        "NW",
        "NE",
    ]
    return (
        (wave_direction_predominant in papelillo_wave_directions)
        | (wave_direction in papelillo_wave_directions)
    ) & (wave_energy >= 100)


def caleta_caballo_low_wind_conditions(
    wave_direction_predominant: str,
    wave_direction: str,
    wave_energy: int,
):
    caleta_caballo_wave_directions = ["N", "NW", "NE"]
    unwanted_wave_directions = ["WNW"]
    return (
        (
            (wave_direction_predominant in caleta_caballo_wave_directions)
            | (wave_direction in caleta_caballo_wave_directions)
        )
        & (wave_direction not in unwanted_wave_directions)
        & (wave_energy >= 100 and wave_energy <= 1000)
    )


def caleta_caballo_conditions(
    wind_direction_predominant: str,
    wave_direction_predominant: str,
    wind_direction: str,
    wave_direction: str,
    wave_energy: int,
):

    return caleta_caballo_favorable_wind(wind_direction_predominant, wind_direction) & (
        caleta_caballo_low_wind_conditions(
            wave_direction_predominant, wave_direction, wave_energy
        )
    )


def san_juan_low_wind_conditions(
    wave_direction_predominant: str,
    wave_direction: str,
    wave_energy: int,
):
    san_juan_wave_directions = ["N", "NW", "NE"]
    unwanted_wave_directions = ["WNW"]
    return (
        (
            (wave_direction_predominant in san_juan_wave_directions)
            | (wave_direction in san_juan_wave_directions)
        )
        & (wave_direction not in unwanted_wave_directions)
        & (wave_energy > 1000)
    )


def san_juan_conditions(
    wind_direction_predominant: str,
    wind_direction: str,
    wave_direction_predominant: str,
    wave_direction: str,
    wave_energy: int,
):

    return san_juan_favorable_wind(wind_direction_predominant, wind_direction) & (
        san_juan_low_wind_conditions(
            wave_direction_predominant, wave_direction, wave_energy
        )
    )


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
    unwanted_wave_directions = ["WNW"]

    return (
        (
            (
                (wind_direction_predominant in bastian_wind_directions)
                | (wind_direction in bastian_wind_directions)
            )
            & (
                (wave_direction_predominant in bastian_wave_directions)
                | (wave_direction in bastian_wave_directions)
            )
            & ((wave_direction not in unwanted_wave_directions))
        )
        & (wind_speed >= 19.0)
        & (tide_percentage >= 50)
    )


def barcarola_conditions(
    wind_direction_predominant: str,
    wave_direction_predominant: str,
    wind_direction: str,
    wave_direction: str,
    wind_speed: float,
    wave_period: int,
    tide_percentage: float,
):

    barcarola_wind_directions = ["NE", "N"]
    barcarola_wave_directions = ["N", "NW", "NE", "E", "S"]
    unwanted_wave_directions = ["WNW"]

    return (
        (
            (
                (wind_direction_predominant in barcarola_wind_directions)
                | (wind_direction in barcarola_wind_directions)
            )
            & (
                (wave_direction_predominant in barcarola_wave_directions)
                | (wave_direction in barcarola_wave_directions)
            )
            & ((wave_direction not in unwanted_wave_directions))
        )
        & (wind_speed >= 19.0)
        & (wave_period >= 10)
        & (tide_percentage <= 50)
    )


def lasanta_conditions(
    wind_direction_predominant: str,
    wave_direction_predominant: str,
    wind_direction: str,
    wave_direction: str,
    wave_energy: int,
):

    return lasanta_favorable_wind(
        wind_direction_predominant, wind_direction
    ) & lasanta_low_wind_conditions(
        wave_direction_predominant, wave_direction, wave_energy
    )


def lasanta_low_wind_conditions(
    wave_direction_predominant: str,
    wave_direction: str,
    wave_energy: int,
):
    lasanta_wave_directions = ["N", "NW", "NE"]
    unwanted_wave_directions = ["WNW"]
    return (
        (
            (wave_direction_predominant in lasanta_wave_directions)
            | (wave_direction in lasanta_wave_directions)
        )
        & (wave_direction not in unwanted_wave_directions)
    ) & (wave_energy >= 100 and wave_energy <= 1000)


def famara_conditions(
    wind_direction_predominant: str,
    wave_direction_predominant: str,
    wind_direction: str,
    wave_direction: str,
    wave_energy: int,
):
    return famara_favorable_wind(wind_direction_predominant, wind_direction) & (
        famara_low_wind_conditions(
            wave_direction_predominant, wave_direction, wave_energy
        )
    )


def famara_low_wind_conditions(
    wave_direction_predominant: str,
    wave_direction: str,
    wave_energy: int,
):
    famara_wave_directions = ["N", "NW", "NE"]
    unwanted_wave_directions = ["WNW"]
    return (
        (
            (wave_direction_predominant in famara_wave_directions)
            | (wave_direction in famara_wave_directions)
        )
        & (wave_direction not in unwanted_wave_directions)
    ) & (wave_energy >= 100 and wave_energy <= 1000)


def big_waves_conditions(
    wave_height: float, wave_direction: str, wave_direction_predominant: str
):
    big_wave_directions = ["N", "NE", "E"]
    unwanted_wave_directions = ["WNW"]
    return (
        (
            (wave_direction_predominant in big_wave_directions)
            | (wave_direction in big_wave_directions)
        )
        & (wave_direction not in unwanted_wave_directions)
        & (wave_height > 2.5)  # Si en 2.5 no hay nada, revisar en 3
    )


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
    east_wind_directions = ["E", "NE"]
    return is_favorable_wind(
        wind_direction_predominant, wind_direction, east_wind_directions
    )


def tiburon_favorable_wind(wind_direction_predominant, wind_direction):
    tiburon_wind_directions = ["W", "NW", "SW"]
    return is_favorable_wind(
        wind_direction_predominant, wind_direction, tiburon_wind_directions
    )


def bajorisco_favorable_wind(wind_direction_predominant, wind_direction):
    risco_wind_directions = ["S", "SE", "E"]
    return is_favorable_wind(
        wind_direction_predominant, wind_direction, risco_wind_directions
    )


def papelillo_favorable_low_wind(wind_direction_predominant, wind_direction):
    east_wind_directions = ["E", "SE"]
    return is_favorable_wind(
        wind_direction_predominant, wind_direction, east_wind_directions
    )


def punta_mujeres_favorable_wind(wind_direction_predominant, wind_direction):
    punta_mujeres_wind_directions = ["N", "NW"]
    return is_favorable_wind(
        wind_direction_predominant, wind_direction, punta_mujeres_wind_directions
    )


def san_juan_favorable_wind(wind_direction_predominant, wind_direction):
    san_juan_wind_directions = ["S", "SE"]
    return is_favorable_wind(
        wind_direction_predominant, wind_direction, san_juan_wind_directions
    )


def caleta_caballo_favorable_wind(wind_direction_predominant, wind_direction):
    caleta_caballo_wind_directions = ["W", "SW", "WNW"]
    return is_favorable_wind(
        wind_direction_predominant, wind_direction, caleta_caballo_wind_directions
    )


def is_favorable_wind(
    wind_direction_predominant: str, wind_direction: str, target_wind_directions: str
):
    return (wind_direction_predominant in target_wind_directions) | (
        wind_direction in target_wind_directions
    )


def get_low_wind_spot(
    wind_direction_predominant,
    wind_direction,
    wave_direction_predominant,
    wave_direction,
    wave_energy,
    tide_percentage,
):
    if famara_low_wind_conditions(
        wave_direction_predominant,
        wave_direction,
        wave_energy,
    ) and famara_favorable_wind(wind_direction_predominant, wind_direction):
        return "Famara"
    elif tiburon_low_wind_conditions(
        wave_direction_predominant,
        wave_direction,
        wave_energy,
    ) and tiburon_favorable_wind(wind_direction_predominant, wind_direction):
        return "Tiburón"
    elif papagayo_low_wind_conditions(
        wave_direction_predominant,
        wave_direction,
        wave_energy,
        tide_percentage,
    ) and papagayo_favorable_wind(wind_direction_predominant, wind_direction):
        return "Papagayo - Montaña Amarilla"
    elif west_swell_high_tide_low_wind_conditions(
        wave_direction_predominant,
        wave_direction,
        wave_energy,
        tide_percentage,
    ) and bajorisco_favorable_wind(wind_direction_predominant, wind_direction):
        return "Bajo el Risco"
    elif papelillo_low_wind_conditions(
        wave_direction_predominant, wave_direction, wave_energy
    ) and papelillo_favorable_low_wind(wind_direction_predominant, wind_direction):
        return "Papelillo"
    elif lasanta_low_wind_conditions(
        wave_direction_predominant,
        wave_direction,
        wave_energy,
    ) and lasanta_favorable_wind(wind_direction_predominant, wind_direction):
        return "La Santa"
    elif san_juan_low_wind_conditions(
        wave_direction_predominant, wave_direction, wave_energy
    ) and san_juan_favorable_wind(wind_direction_predominant, wind_direction):
        return "San Juan - Cagao - El Muelle"
    elif punta_mujeres_low_wind_conditions(
        wave_direction_predominant, wave_direction, wave_energy
    ) and punta_mujeres_favorable_wind(wind_direction_predominant, wind_direction):
        return "Punta Mujeres"
    elif caleta_caballo_low_wind_conditions(
        wave_direction_predominant, wave_direction, wave_energy
    ) and caleta_caballo_favorable_wind(wind_direction_predominant, wind_direction):
        return "Caleta Caballo"
    elif famara_low_wind_conditions(
        wave_direction_predominant,
        wave_direction,
        wave_energy,
    ):
        return "Famara"
    elif san_juan_low_wind_conditions(
        wave_direction_predominant,
        wave_direction,
        wave_energy,
    ):
        return "San Juan - Cagao - El Muelle"
    else:
        return "No Clasificado"


def is_low_wind(wind_speed: float) -> bool:
    return wind_speed < 10.0


# 304 es ONO, 305 es NO, considerar fuerza oeste hasta 310
def generate_spot_name(
    wind_direction_predominant: str,
    wind_direction: str,
    wind_speed: float,
    tide_percentage: int,
    wave_period: int,
    wave_energy: int,
    wave_direction: str,
    wave_direction_predominant: str,
) -> str:
    if is_low_wind(wind_speed=wind_speed):
        spot = get_low_wind_spot(
            wind_direction_predominant=wind_direction_predominant,
            wind_direction=wind_direction,
            wave_direction_predominant=wave_direction_predominant,
            wave_direction=wave_direction,
            wave_energy=wave_energy,
            tide_percentage=tide_percentage,
        )
        return spot
    elif barcarola_conditions(
        wind_direction_predominant=wind_direction_predominant,
        wave_direction_predominant=wave_direction_predominant,
        wind_direction=wind_direction,
        wave_direction=wave_direction,
        wind_speed=wind_speed,
        tide_percentage=tide_percentage,
        wave_period=wave_period,
    ):
        return "Barcarola"
    elif bastian_conditions(
        wind_direction_predominant=wind_direction_predominant,
        wave_direction_predominant=wave_direction_predominant,
        wind_direction=wind_direction,
        wave_direction=wave_direction,
        wind_speed=wind_speed,
        tide_percentage=tide_percentage,
    ):
        return "Bastián"
    elif punta_mujeres_conditions(
        wind_direction_predominant=wind_direction_predominant,
        wave_direction_predominant=wave_direction_predominant,
        wind_direction=wind_direction,
        wave_direction=wave_direction,
        wave_energy=wave_energy,
    ):
        return "Punta Mujeres"
    elif tiburon_conditions(
        wind_direction_predominant=wind_direction_predominant,
        wave_direction_predominant=wave_direction_predominant,
        wind_direction=wind_direction,
        wave_direction=wave_direction,
        wave_energy=wave_energy,
    ):
        return "Tiburón"
    elif papagayo_conditions(
        wind_direction_predominant=wind_direction_predominant,
        wave_direction_predominant=wave_direction_predominant,
        wind_direction=wind_direction,
        wave_direction=wave_direction,
        wave_energy=wave_energy,
        tide_percentage=tide_percentage,
    ):
        return "Papagayo - Montaña Amarilla"

    elif bajorisco_conditions(
        wind_direction_predominant=wind_direction_predominant,
        wave_direction_predominant=wave_direction_predominant,
        wind_direction=wind_direction,
        wave_direction=wave_direction,
        wave_energy=wave_energy,
        tide_percentage=tide_percentage,
    ):
        return "Bajo el Risco"
    elif papelillo_conditions(
        wave_direction_predominant=wave_direction_predominant,
        wind_direction_predominant=wind_direction_predominant,
        wave_direction=wave_direction,
        wind_direction=wind_direction,
        wave_energy=wave_energy,
    ):
        return "Papelillo"
    elif caleta_caballo_conditions(
        wind_direction_predominant=wind_direction_predominant,
        wave_direction_predominant=wave_direction_predominant,
        wind_direction=wind_direction,
        wave_direction=wave_direction,
        wave_energy=wave_energy,
    ):
        return "Caleta Caballo"
    elif famara_conditions(
        wind_direction_predominant=wind_direction_predominant,
        wave_direction_predominant=wave_direction_predominant,
        wind_direction=wind_direction,
        wave_direction=wave_direction,
        wave_energy=wave_energy,
    ):
        return "Famara"
    elif lasanta_conditions(
        wind_direction_predominant=wind_direction_predominant,
        wave_direction_predominant=wave_direction_predominant,
        wind_direction=wind_direction,
        wave_direction=wave_direction,
        wave_energy=wave_energy,
    ):
        return "La Santa"
    elif san_juan_conditions(
        wind_direction_predominant=wind_direction_predominant,
        wind_direction=wind_direction,
        wave_direction_predominant=wave_direction_predominant,
        wave_direction=wave_direction,
        wave_energy=wave_energy,
    ):
        return "San Juan - Cagao - El Muelle"
    else:
        return "No Clasificado"


def generate_spot_names(forecast: Dict[str, list]) -> list:
    spot_names = []
    wind_direction_predominant = forecast["wind_direction_predominant"]
    wave_direction_predominant = forecast["wave_direction_predominant"]
    wind_direction = forecast["wind_direction"]
    wave_direction = forecast["wave_direction"]
    wind_speed = forecast["wind_speed"]
    wave_period = forecast["wave_period"]
    tide_percentage = forecast["tide_percentage"]
    energy = forecast["energy"]

    for wid_predominant, wad_predominant, wid, wad, ws, tp, wp, e in zip(
        wind_direction_predominant,
        wave_direction_predominant,
        wind_direction,
        wave_direction,
        wind_speed,
        tide_percentage,
        wave_period,
        energy,
    ):
        spot_name = generate_spot_name(
            wid_predominant, wid, ws, tp, wp, e, wad, wad_predominant
        )
        spot_names.append(spot_name)
    return spot_names


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
        times = df["time"]
        df = df.with_columns(pl.col("datetime").dt.convert_time_zone("UTC"))
        datetimes = df["datetime"]
        _6_AM = time(hour=6, minute=0, second=0, microsecond=0)
        _19_PM = time(hour=19, minute=0, second=0, microsecond=0)
        now = datetime.now(timezone.utc)
        mask = (times >= _6_AM) & (times <= _19_PM) & (datetimes >= now)
        df = df.filter(mask)

        common_columns = [
            "date_name",
            "date_friendly",
            "time_friendly",
            "energy",
            "wave_period",
            "wind_direction",
            "wind_direction_predominant",
            "wave_direction",
            "wind_speed",
            "tide_percentage",
            "nearest_tide",
            "tide",
            "datetime",
            "date",
            "time",
            "time_graph",
            "spot_name",
            "wave_direction_predominant",
            "wave_height",
            "wind_direction_degrees",
            "wave_direction_degrees",
        ]
        df = df[common_columns]
    return df


def degrees_to_direction(degrees):
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    index = round(degrees / 45) % 8
    return directions[index]


def datetime_to_frontend_str(dt: datetime) -> str:
    return dt.strftime(FRONT_END_DATE_FORMAT).capitalize()


def construct_date_selection_list(
    min_value: datetime, max_value: datetime, scraped_datetime_list: list
) -> list:
    date_selection = []
    for scraped_datetime in scraped_datetime_list:
        if scraped_datetime >= min_value and scraped_datetime <= max_value:
            date_selection.append(scraped_datetime)
    return date_selection


def datestr_to_datetime(dtstr, format) -> datetime:
    return datetime.strptime(dtstr, format)


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


def degrees_to_direction(degrees: int) -> str:

    compass_directions = [
        "N",
        "NNE",
        "NE",
        "ENE",
        "E",
        "ESE",
        "SE",
        "SSE",
        "S",
        "SSW",
        "SW",
        "WSW",
        "W",
        "WNW",
        "NW",
        "NNW",
    ]

    sector_size = 360 / len(compass_directions)
    degrees = degrees % 360
    index = int((degrees + sector_size / 2) // sector_size) % len(compass_directions)
    return compass_directions[index]


def generate_forecast_moments(initstamp, hours):
    init_datetime = datetime.fromtimestamp(initstamp, tz=timezone.utc).replace(
        tzinfo=None
    )
    moments = [init_datetime + timedelta(hours=hour) for hour in hours]

    return moments
