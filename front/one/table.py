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
import pandas as pd
from datetime import datetime, timedelta, timezone
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode

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


def plot_graph(add_data: str, data: pl.DataFrame):
    st.header(f"Energía por días ({add_data})", divider="rainbow")

    source = data.to_pandas()
    now = datetime.now(timezone.utc)
    highlight = alt.selection_point(on="mouseover", fields=["spot_name"], nearest=True)
    base = alt.Chart(source).encode(
        x=alt.X("datetime:T", title="Día y Hora"),
        y=alt.Y("energy:Q", title="Energía (kJ)", scale=alt.Scale(zero=False)),
        color=alt.Color(
            "spot_name:N", title="Playa", scale=alt.Scale(scheme="tableau10")
        ),
        tooltip=[
            alt.Tooltip("datetime:T", format="%H:%M %d/%m", title="Hora"),
            alt.Tooltip("spot_name:N", title="Playa"),
            alt.Tooltip("energy:Q", title="Energía (kJ)"),
            alt.Tooltip("wave_height:Q", title="Altura (m)"),
            alt.Tooltip("wave_period:Q", title="Periodo (s)"),
        ],
    )
    lines = (
        base.mark_line(strokeWidth=3, interpolate="monotone")
        .encode(size=alt.condition(~highlight, alt.value(2), alt.value(5)))
        .add_params(highlight)
    )

    points = base.mark_point(filled=True, size=60).encode(
        opacity=alt.condition(~highlight, alt.value(0.3), alt.value(1))
    )
    now_df = pd.DataFrame({"now": [now]})
    rule = (
        alt.Chart(now_df)
        .mark_rule(color="#ff4b4b", strokeDash=[5, 5], strokeWidth=2)
        .encode(x="now:T")
    )

    text = (
        alt.Chart(now_df)
        .mark_text(
            align="left",
            dx=5,
            dy=-180,
            text="📍 AHORA",
            color="#ff4b4b",
            fontWeight="bold",
        )
        .encode(x="now:T")
    )
    final_chart = (
        (lines + points + rule + text)
        .properties(width="container", height=450)
        .interactive()
    )

    st.altair_chart(final_chart, width="stretch")


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


def plot_forecast_as_table():
    st.set_page_config(layout="wide")
    st.markdown(
        "<style>.ag-theme-alpine {height: auto !important; min-height: 100px;}</style>",
        unsafe_allow_html=True,
    )

    st.title("LANZAROTE (WINDGURU)")

    retries = 0
    while retries <= RETRIES:
        initial_forecast = load_windguru_forecast()
        if not initial_forecast.is_empty():
            break
        else:
            retries += 1
    if retries > RETRIES:
        st.error("No se pudo obtener el forecast")
        return

    st.session_state.forecast_df = initial_forecast
    scraped_datetime_list = list(
        set(st.session_state.forecast_df["datetime"].to_list())
    )
    scraped_date_list = set([date.date() for date in scraped_datetime_list])
    date_name_list = list(set(st.session_state.forecast_df["date_name"].to_list()))
    all_beaches = list(set(st.session_state.forecast_df["spot_name"].to_list()))

    with st.sidebar:
        st.header("Filtros de Forecast")
        date_name_selection = st.multiselect(
            "Cuándo?:", date_name_list, default=date_name_list
        )

        today = datetime.now().date()
        next_days = (datetime.now() + timedelta(days=17)).date()
        selected_date_range_datetime = st.date_input(
            "Rango de fechas", (today, next_days), today, next_days, format="DD/MM/YYYY"
        )

        selected_wave_energy = plot_selected_wave_energy()
        selected_wind_speed = plot_selected_wind_speed()
        beach_selection = st.multiselect("Playa:", all_beaches, default=all_beaches)

    date_selection = []
    if len(selected_date_range_datetime) == 2:
        date_selection = construct_date_selection_list(
            selected_date_range_datetime[0],
            selected_date_range_datetime[1],
            scraped_date_list,
        )
    if not date_selection:
        date_selection = scraped_date_list

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
    data = df.filter(mask)

    # TODO put in a method
    if not data.is_empty():
        next_forecast = data.sort("datetime").head(1).to_dicts()[0]
        now = datetime.now(timezone.utc)
        target_time = next_forecast["datetime"]

        if target_time.tzinfo is None:
            target_time = target_time.replace(tzinfo=timezone.utc)

        diff = target_time - now
        total_seconds = int(diff.total_seconds())
        if total_seconds <= 0:
            tiempo_display = "Ahora"
        else:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
        if hours > 0:
            tiempo_display = f"En {hours}h y {minutes}min"
        else:
            tiempo_display = f"En {minutes}min"

        st.subheader(f"⏱️ Próxima Sesión: {next_forecast['spot_name']}", divider="blue")
        c1, c2, c3, c4, c5 = st.columns(5)

        with c1:
            st.metric(
                "Inicio",
                f"A las {next_forecast['time_friendly']}",
                tiempo_display,
                delta_arrow="off",
            )

        with c2:
            st.metric(
                "Energía",
                f"{next_forecast['energy']} kJ",
            )

        with c3:
            st.metric(
                "Swell",
                f"{next_forecast['wave_height']}m | {next_forecast['wave_period']}s",
                f"{next_forecast['wave_direction']}",
                delta_arrow="off",
            )

        with c4:
            st.metric(
                "Viento",
                f"{next_forecast['wind_speed']} kn",
                next_forecast["wind_direction"],
                delta_arrow="off",
            )

        with c5:
            st.metric(
                "Marea",
                f"{next_forecast['tide_percentage']}%",
                next_forecast["tide"],
                delta_arrow="off",
            )

    data_other = data.filter(~pl.col("wave_direction").is_in(["W", "WNW"]))
    plot_graph("fuerza norte", data_other)

    data_west_wave = data.filter(pl.col("wave_direction").is_in(["W", "WNW"]))
    if not data_west_wave.is_empty():
        plot_graph("fuerza oeste", data_west_wave)

    grouped_data = data.group_by("spot_name").agg(
        pl.col("datetime").min().alias("datetime")
    )
    grouped_data = grouped_data.sort("datetime", descending=False)

    # TODO put in a method
    with st.container():
        for i, row in enumerate(grouped_data.to_dicts()):
            spot_name = row["spot_name"]
            group_df = data.filter(pl.col("spot_name") == spot_name)

            with st.expander(f"Spot: {spot_name} ({group_df.height} times)"):
                group_df = group_df.with_columns(
                    [
                        (
                            pl.col("wind_direction")
                            + " ("
                            + pl.col("wind_direction_degrees").cast(pl.Utf8)
                            + "º)"
                        ).alias("wind_unified"),
                        (
                            pl.col("wave_direction")
                            + " ("
                            + pl.col("wave_direction_degrees").cast(pl.Utf8)
                            + "º)"
                        ).alias("wave_unified"),
                        (
                            pl.col("nearest_tide")
                            + " ("
                            + pl.col("tide_percentage").cast(pl.Utf8)
                            + "%)"
                        ).alias("tide_unified"),
                    ]
                )

                date_friendly = group_df["date_friendly"].to_list()
                time_friendly = group_df["time_friendly"].to_list()
                date_names = group_df["date_name"].to_list()

                forecast_to_plot = (
                    group_df.drop(
                        [
                            "spot_name",
                            "date",
                            "time",
                            "time_graph",
                            "wind_direction",
                            "wind_direction_degrees",
                            "wave_direction",
                            "wave_direction_degrees",
                            "date_friendly",
                            "time_friendly",
                            "date_name",
                            "nearest_tide",
                            "tide_percentage",
                        ]
                    )
                    .sort("datetime")
                    .rename(
                        {
                            "wave_unified": "wave_direction",
                            "wind_unified": "wind_direction",
                            "tide_unified": "nearest_tide",
                        }
                    )
                )

                forecast_to_plot = forecast_to_plot.drop(["datetime"])

                order_surf = [
                    "energy",
                    "nearest_tide",
                    "tide",
                    "wind_direction",
                    "wind_direction_predominant",
                    "wave_height",
                    "wave_period",
                    "wave_direction",
                    "wave_direction_predominant",
                    "wind_speed",
                ]
                forecast_to_plot = forecast_to_plot.select(order_surf)

                forecast_columns = [col.upper() for col in forecast_to_plot.columns]
                rotated_df = forecast_to_plot.transpose(include_header=False)
                rotated_df.insert_column(0, pl.Series("column names", forecast_columns))
                rotated_df_pd = rotated_df.to_pandas()

                gb = GridOptionsBuilder.from_dataframe(rotated_df_pd)
                gb.configure_default_column(
                    wrapText=True,
                    autoHeight=True,
                    editable=False,
                    resizable=True,
                    suppressMovable=True,
                )
                gb.configure_grid_options(domLayout="autoHeight")
                gb.configure_column(
                    "column names",
                    pinned="left",
                    cellStyle={
                        "fontWeight": "bold",
                        "backgroundColor": "#f8f9fb",
                        "borderRight": "1px solid #d3d3d3",
                    },
                    width=150,
                )
                gb.configure_column("column names", suppressMenu=True)
                grid_options = gb.build()
                column_defs = grid_options["columnDefs"]

                for idx, col in enumerate(column_defs[1:]):
                    name = unicodedata.normalize("NFC", date_names[idx])
                    if name in ["Hoy", "Mañana", "Pasado"]:
                        col["headerName"] = f"{time_friendly[idx]} {name}"
                    else:
                        col["headerName"] = f"{time_friendly[idx]} {date_friendly[idx]}"

                AgGrid(
                    rotated_df_pd,
                    gridOptions=grid_options,
                    theme="alpine",
                    key=f"grid_{spot_name}_{i}",
                    columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
                    enable_enterprise_modules=False,
                )
