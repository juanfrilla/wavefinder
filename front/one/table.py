import streamlit as st
import time
from utils import final_forecast_format, construct_date_selection_list
from multi import multithread
from scrapers.windguru import Windguru
from scrapers.tides import TidesScraper
import altair as alt
import polars as pl
from datetime import datetime, timedelta
from urls.windguru import WINDGURU_URLS

DEFAULT_MIN_WAVE_PERIOD = 0
DEFAULT_WAVE_HEIGHT = 0.0
DEFAULT_MIN_WAVE_ENERGY = 100


def get_list_of_spots_sorted_by_param(param, grouped_data):
    max_energy_per_spot = grouped_data.groupby("spot_name").agg(
        pl.col(param).max().alias("max_energy")
    )

    return max_energy_per_spot.sort("max_energy", descending=True)[
        "spot_name"
    ].to_list()


def plot_graph(variable):
    st.header(f"{variable} per day", divider="rainbow")
    data = st.session_state.forecast_df
    chart = (
        alt.Chart(data)
        .mark_line(strokeWidth=3, point=True)
        .encode(
            x="datetime:T",
            y=alt.Y(f"{variable}:Q", impute=alt.ImputeParams(value=None)),
            color="spot_name:N",
            detail="date_dt:T",
            tooltip=[
                alt.Tooltip("date_dt:T", format="%d/%m/%Y", title="Date"),
                alt.Tooltip("time_cor:N", title="Time"),
                "energy:Q",
                "spot_name:N",
                "wave_height:Q",
                "wind_speed:Q",
                "wind_direction:N",
                "wave_direction:N",
                "wave_period:Q",
            ],
        )
        .properties(width=600, height=400)
        .configure_legend(orient="right")
    )

    st.container()

    zoomed_chart = chart.interactive().properties(width=600, height=400)

    st.altair_chart(zoomed_chart, use_container_width=True)


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


def plot_selected_wave_height(default_wave_height):
    min_wave_height = float(st.session_state.forecast_df["wave_height"].min())
    max_wave_height = float(st.session_state.forecast_df["wave_height"].max())
    if max_wave_height < default_wave_height:
        default_wave_height_selection = (1.0, default_wave_height)
    else:
        default_wave_height_selection = (default_wave_height, max_wave_height)
    return st.slider(
        "Altura de las olas (m)",
        min_wave_height,
        max_wave_height,
        default_wave_height_selection,
        0.1,
    )


def plot_selected_swell_height(default_swell_height=2.0):
    try:
        min_swell_height = float(st.session_state.forecast_df["swell_height"].min())
        max_swell_height = float(st.session_state.forecast_df["swell_height"].max())
        if max_swell_height < default_swell_height:
            default_swell_height_selection = (1.0, default_swell_height)
        else:
            default_swell_height_selection = (default_swell_height, max_swell_height)
        return st.slider(
            "Altura del mar de fondo - swell (m)",
            min_swell_height,
            max_swell_height,
            default_swell_height_selection,
            0.1,
        )
    except Exception as e:
        return None


def plot_selected_wave_period():
    min_wave_period = int(st.session_state.forecast_df["wave_period"].min())
    max_wave_period = int(st.session_state.forecast_df["wave_period"].max())
    if max_wave_period < DEFAULT_MIN_WAVE_PERIOD:
        default_wave_period_selection = (5, DEFAULT_MIN_WAVE_PERIOD)
    else:
        default_wave_period_selection = (DEFAULT_MIN_WAVE_PERIOD, max_wave_period)
    return st.slider(
        "Periodo de las olas (s)",
        min_wave_period,
        max_wave_period,
        default_wave_period_selection,
        1,
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


@st.cache_data(ttl="3600")
def load_windguru_forecast():
    url = "https://www.windguru.cz/49328"
    tide_scraper = TidesScraper()
    tides = tide_scraper.tasks()
    start_time = time.time()
    windguru = Windguru()
    df = windguru.scrape(url, tides)
    df = final_forecast_format(df)
    if "datetime" in df.columns:
        df = df.sort("datetime", descending=False)
    print("--- %s seconds ---" % (time.time() - start_time))

    return df


def custom_sort_key(item):
    custom_order = {"Hoy": 1, "Mañana": 2, "Pasado": 3, "Otro día": 4}
    return custom_order.get(item, 5)


def plot_forecast_as_table():
    st.set_page_config(layout="wide")

    st.title("LANZAROTE (WINDGURU)")

    initial_forecast = load_windguru_forecast()
    st.session_state.forecast_df = initial_forecast
    scraped_datetime_list = list(
        set(st.session_state.forecast_df["datetime"].to_list())
    )
    scraped_date_list = set([date.date() for date in scraped_datetime_list])
    date_name_list = list(set(st.session_state.forecast_df["date_name"].to_list()))
    all_beaches = list(set(st.session_state.forecast_df["spot_name"].to_list()))

    # CREATE MULTISELECT
    date_name_selection = st.multiselect(
        "Nombre del día:", date_name_list, default=date_name_list
    )

    today = datetime.now().date()
    next_days = (datetime.now() + timedelta(days=17)).date()
    selected_date_range_datetime = st.date_input(
        "Selecciona el rango de fechas",
        (today, next_days),
        today,
        next_days,
        format="DD/MM/YYYY",
    )
    date_selection = []
    if len(selected_date_range_datetime) == 2:
        min_value = selected_date_range_datetime[0]
        max_value = selected_date_range_datetime[1]
        date_selection = construct_date_selection_list(
            min_value, max_value, scraped_date_list
        )
    selected_wave_height = plot_selected_wave_height(DEFAULT_WAVE_HEIGHT)
    selected_swell_height = plot_selected_swell_height()
    selected_wave_period = plot_selected_wave_period()
    selected_wave_energy = plot_selected_wave_energy()
    selected_wind_speed = plot_selected_wind_speed()

    beach_selection = st.multiselect("Playa:", all_beaches, default=all_beaches)
    if date_selection == []:
        date_selection = scraped_date_list

    date_condition = st.session_state.forecast_df["date"].is_in(date_selection)

    date_name_condition = st.session_state.forecast_df["date_name"].is_in(
        date_name_selection
    )
    beach_condition = st.session_state.forecast_df["spot_name"].is_in(beach_selection)
    wave_height_condition = (
        st.session_state.forecast_df["wave_height"] >= selected_wave_height[0]
    ) & (st.session_state.forecast_df["wave_height"] <= selected_wave_height[1])
    wave_period_condition = (
        st.session_state.forecast_df["wave_period"] >= selected_wave_period[0]
    ) & (st.session_state.forecast_df["wave_period"] <= selected_wave_period[1])
    wind_speed_condition = (
        st.session_state.forecast_df["wind_speed"] >= selected_wind_speed[0]
    ) & (st.session_state.forecast_df["wind_speed"] <= selected_wind_speed[1])
    if selected_swell_height:
        swell_height_condition = (
            st.session_state.forecast_df["swell_height"] >= selected_swell_height[0]
        ) & (st.session_state.forecast_df["swell_height"] <= selected_swell_height[1])
    else:
        swell_height_condition = True

    wave_energy_condition = (
        st.session_state.forecast_df["energy"] >= selected_wave_energy[0]
    ) & (st.session_state.forecast_df["energy"] <= selected_wave_energy[1])

    mask = (
        date_condition
        & date_name_condition
        & beach_condition
        & wave_height_condition
        & wave_period_condition
        & wind_speed_condition
        & swell_height_condition
        & wave_energy_condition
    )

    st.session_state.forecast_df = st.session_state.forecast_df.filter(mask)
    date = st.session_state.forecast_df["datetime"].dt.date().to_list()
    time = [
        element.replace(":", r"\:")
        for element in st.session_state.forecast_df["time"].to_list()
    ]
    st.session_state.forecast_df = st.session_state.forecast_df.with_columns(
        pl.Series(name="date_dt", values=date)
    )

    st.session_state.forecast_df = st.session_state.forecast_df.with_columns(
        pl.Series(name="time_cor", values=time)
    )
    plot_graph("energy")
    grouped_data = st.session_state.forecast_df.group_by("spot_name").agg(
        pl.col("datetime").min().alias("datetime")
    )
    if "datetime" in grouped_data.columns:
        grouped_data = grouped_data.sort("datetime", descending=False)
    else:
        st.warning("'datetime' column not found, skipping sort.")

    with st.container():
        for i in range(len(grouped_data)):
            spot_name = grouped_data[i]["spot_name"].to_numpy()[0]
            group_df = st.session_state.forecast_df.filter(
                pl.col("spot_name") == spot_name
            )

            st.subheader(f"Spot: {spot_name}")
            forecast_df_dropped = group_df.drop("spot_name")
            forecast_df_dropped = forecast_df_dropped.unique(subset=["datetime"]).drop(
                "datetime"
            )
            st.dataframe(
                forecast_df_dropped,
                hide_index=True,
            )
