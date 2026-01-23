import os
import json
import time
import unicodedata
import streamlit as st
from utils import final_forecast_format, construct_date_selection_list
from scrapers.windguru import Windguru
from scrapers.tides import TidesScraperLanzarote
import altair as alt
import polars as pl
from datetime import datetime, timedelta
from st_aggrid import AgGrid, GridOptionsBuilder

DEFAULT_MIN_WAVE_PERIOD = 0
DEFAULT_WAVE_HEIGHT = 0.0
DEFAULT_MIN_WAVE_ENERGY = 100
RETRIES = 100
CACHE_TTL_SECONDS = 3600
WAVES_CACHE_PATH = "data/waves.json"
WIND_CACHE_PATH = "data/wind.json"
TIDES_CACHE_PATH = "data/tides.json"


def get_list_of_spots_sorted_by_param(param, grouped_data):
    max_energy_per_spot = grouped_data.groupby("spot_name").agg(
        pl.col(param).max().alias("max_energy")
    )

    return max_energy_per_spot.sort("max_energy", descending=True)[
        "spot_name"
    ].to_list()


def plot_graph(variable, add_data: str, data: pl.DataFrame):
    st.header(f"{variable} {add_data} per day", divider="rainbow")
    num_categories = data["spot_name"].n_unique()
    chart = (
        alt.Chart(data.to_pandas())
        .mark_line(strokeWidth=3, point=True)
        .encode(
            x="datetime:T",
            y=alt.Y(f"{variable}:Q", impute=alt.ImputeParams(value=None)),
            color=alt.Color(
                "spot_name:N",
                scale=alt.Scale(
                    scheme="category20" if num_categories <= 20 else "tableau10"
                ),
            ),
            detail="date:T",
            tooltip=[
                alt.Tooltip("date:T", format="%d/%m/%Y", title="Date"),
                alt.Tooltip("time_graph:N", title="Time"),
                "energy:Q",
                "spot_name:N",
                "wave_height:Q",
                "wind_speed:Q",
                "wind_direction:N",
                "wave_direction:N",
                "wave_period:Q",
                "tide_percentage:Q",
            ],
        )
        .properties(width=600, height=400)
        .configure_legend(orient="right")
    )

    st.container()

    zoomed_chart = chart.interactive().properties(width=600, height=400)

    st.altair_chart(zoomed_chart, width="stretch")


def plot_selected_wind_speed():
    min_wind_speed = float(st.session_state.forecast_df["wind_speed"].min())
    max_wind_speed = float(st.session_state.forecast_df["wind_speed"].max())
    default_wind_speed_selection = (min_wind_speed, max_wind_speed)
    return st.slider(
        "Velocidad del viento (nudos)",
        min_wind_speed,
        max_wind_speed,
        default_wind_speed_selection,
        0.1,
    )


def get_default_wind_approval_selection(wind_approval_list):
    if (
        "Viento Favorable" in wind_approval_list
        and "Viento No Favorable" in wind_approval_list
    ):
        return ["Viento Favorable"]
    elif len(wind_approval_list) == 1 and "Viento No Favorable" in wind_approval_list:
        return ["Viento No Favorable"]
    elif len(wind_approval_list) == 1 and "Viento Favorable" in wind_approval_list:
        return ["Viento Favorable"]
    return []


def plot_selected_wave_energy():
    min_wave_energy = int(st.session_state.forecast_df["energy"].min())
    max_wave_energy = int(st.session_state.forecast_df["energy"].max())
    if max_wave_energy < DEFAULT_MIN_WAVE_ENERGY:
        default_wave_energy_selection = (0, DEFAULT_MIN_WAVE_ENERGY)
    else:
        default_wave_energy_selection = (DEFAULT_MIN_WAVE_ENERGY, max_wave_energy)
    return st.slider(
        "Energía de las olas (kJ)",
        min_wave_energy,
        max_wave_energy,
        default_wave_energy_selection,
        1,
    )


def load_cache(filepath):
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r") as f:
        data = json.load(f)
    if time.time() - data["timestamp"] > CACHE_TTL_SECONDS:
        return None
    return data["payload"]


def save_cache(filepath, payload):
    with open(filepath, "w") as f:
        json.dump({"timestamp": time.time(), "payload": payload}, f)


def scrape_waves_cached():
    cached = load_cache(WAVES_CACHE_PATH)
    if cached is not None:
        return cached
    windguru = Windguru()
    waves_response = windguru.get_waves_from_api(id_spot="49328")
    rjson = waves_response.json()
    save_cache(WAVES_CACHE_PATH, rjson)
    return rjson


def scrape_wind_cached():
    cached = load_cache(WIND_CACHE_PATH)
    if cached is not None:
        return cached
    windguru = Windguru()
    wind_response = windguru.get_wind_from_api(id_spot="49328")
    rjson = wind_response.json()
    save_cache(WIND_CACHE_PATH, rjson)
    return rjson


def scrape_tides_cached():
    cached = load_cache(TIDES_CACHE_PATH)
    if cached is not None:
        return cached
    tide_scraper = TidesScraperLanzarote()
    tides = tide_scraper.tasks()
    save_cache(TIDES_CACHE_PATH, tides)
    return tides


def load_windguru_forecast():
    waves_data = scrape_waves_cached()
    wind_data = scrape_wind_cached()
    tides = scrape_tides_cached()
    windguru = Windguru()
    df = windguru.scrape_with_request(waves_data, wind_data, tides)
    df = final_forecast_format(df)

    return df


def custom_sort_key(item):
    custom_order = {"Hoy": 1, "Mañana": 2, "Pasado": 3, "Otro día": 4}
    return custom_order.get(item, 5)


def plot_forecast_as_table():
    retries = 0
    st.set_page_config(layout="wide")
    st.title("LANZAROTE (WINDGURU)")

    # Fetch forecast data with retries
    while retries <= RETRIES:
        initial_forecast = load_windguru_forecast()
        if not initial_forecast.is_empty():
            break
        else:
            retries += 1
            windguru_scraper = Windguru()
            response = windguru_scraper.windguru_request()
            if response.status_code != 200:
                print(response.status_code)
                print(response.text)
            print("El forecast está vacío")
    if retries > RETRIES:
        st.error("No se pudo obtener el forecast")

    st.session_state.forecast_df = initial_forecast

    # Extract lists for filters
    scraped_datetime_list = list(
        set(st.session_state.forecast_df["datetime"].to_list())
    )
    scraped_date_list = set([date.date() for date in scraped_datetime_list])
    date_name_list = list(set(st.session_state.forecast_df["date_name"].to_list()))
    all_beaches = list(set(st.session_state.forecast_df["spot_name"].to_list()))

    # SIDEBAR FILTERS
    with st.sidebar:
        st.header("Filtros de Forecast")
        # Date names
        date_name_selection = st.multiselect(
            "Cuándo?:", date_name_list, default=date_name_list
        )

        # Date range
        today = datetime.now().date()
        next_days = (datetime.now() + timedelta(days=17)).date()
        selected_date_range_datetime = st.date_input(
            "Rango de fechas",
            (today, next_days),
            today,
            next_days,
            format="DD/MM/YYYY",
        )

        # Wave energy & wind speed sliders
        selected_wave_energy = plot_selected_wave_energy()
        selected_wind_speed = plot_selected_wind_speed()

        # Beach selection
        beach_selection = st.multiselect("Playa:", all_beaches, default=all_beaches)

    # Construct selected date list
    date_selection = []
    if len(selected_date_range_datetime) == 2:
        min_value = selected_date_range_datetime[0]
        max_value = selected_date_range_datetime[1]
        date_selection = construct_date_selection_list(
            min_value, max_value, scraped_date_list
        )
    if date_selection == []:
        date_selection = scraped_date_list

    # FILTER DATA
    df = st.session_state.forecast_df
    mask = (
        df["date"].is_in(date_selection)
        & df["date_name"].is_in(date_name_selection)
        & df["spot_name"].is_in(beach_selection)
        & (df["wind_speed"] >= selected_wind_speed[0])
        & (df["wind_speed"] <= selected_wind_speed[1])
        & (df["energy"] >= selected_wave_energy[0])
        & (df["energy"] <= selected_wave_energy[1])
    )
    st.session_state.forecast_df = df.filter(mask)

    data = st.session_state.forecast_df
    data_other = data.filter(~pl.col("wave_direction").is_in(["W", "WNW"]))
    plot_graph("energy", "north swell", data_other)

    data_west_wave = data.filter(pl.col("wave_direction").is_in(["W", "WNW"]))
    if not data_west_wave.is_empty():
        plot_graph("energy", "west swell", data_west_wave)

    # Display first row summary
    grouped_data = data.group_by("spot_name").agg(
        pl.col("datetime").min().alias("datetime")
    )
    grouped_data = grouped_data.sort("datetime", descending=False)

    st.dataframe(data.drop(["datetime", "date", "time", "time_graph"]).head(1))

    # Detailed spot forecast
    with st.container():
        for i in range(len(grouped_data)):
            spot_name = grouped_data[i]["spot_name"].to_numpy()[0]
            group_df = data.filter(pl.col("spot_name") == spot_name)
            num_rows = group_df.height

            with st.expander(f"Spot: {spot_name} ({num_rows} times)"):
                forecast_df_dropped = (
                    group_df.drop("spot_name")
                    .drop("date")
                    .drop("time")
                    .drop("time_graph")
                )
                forecast_df_dropped.sort("datetime", descending=False)

                date_friendly = forecast_df_dropped["date_friendly"].to_list()
                time_friendly = forecast_df_dropped["time_friendly"].to_list()
                date_name = forecast_df_dropped["date_name"].to_list()

                forecast_to_plot = forecast_df_dropped.drop("datetime")
                forecast_columns = [
                    column.upper() for column in forecast_to_plot.columns
                ]
                rotated_df = forecast_to_plot.transpose(include_header=False)
                rotated_df.insert_column(0, pl.Series("column names", forecast_columns))

                rotated_df_pd = rotated_df.to_pandas()

                gb = GridOptionsBuilder.from_dataframe(rotated_df_pd)
                gb.configure_default_column(
                    wrapText=True, autoHeight=True, editable=False
                )
                gb.configure_grid_options(domLayout="normal")
                gb.configure_column(
                    "column names", pinned="left", cellStyle={"fontWeight": "bold"}
                )

                grid_options = gb.build()
                column_defs = grid_options["columnDefs"]

                for col, name, date, time in zip(
                    column_defs[1:], date_name, date_friendly, time_friendly
                ):
                    norm_name = unicodedata.normalize("NFC", name)
                    if norm_name in [
                        unicodedata.normalize("NFC", s)
                        for s in ["Hoy", "Mañana", "Pasado"]
                    ]:
                        col["headerName"] = f"{time} {name}"
                    else:
                        col["headerName"] = f"{date} {time}"

                    AgGrid(
                        rotated_df_pd,
                        gridOptions=grid_options,
                        fit_columns_on_grid_load=True,
                        theme="alpine",
                        enable_enterprise_modules=False,
                        key=f"grid_{spot_name}_{i}",
                    )
