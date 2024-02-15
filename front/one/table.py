import streamlit as st
import time
from utils import final_forecast_format
from multi import multithread
from scrapers.windfinder import WindFinder
from scrapers.windguru import Windguru
from scrapers.sforecast import SurfForecast
from scrapers.surfline import Surfline
from scrapers.windyapp import WindyApp
from scrapers.wisuki import Wisuki
from scrapers.windycom import WindyCom
from scrapers.worldbeachguide import WorldBeachGuide
from scrapers.tides import TidesScraper
import altair as alt
import polars as pl
from datetime import datetime

DEFAULT_MIN_WAVE_PERIOD = 7
DEFAULT_WAVE_HEIGHT = 0.9
DEFAULT_MIN_WAVE_ENERGY = 100


def get_list_of_spots_sorted_by_param(param, grouped_data):
    max_energy_per_spot = grouped_data.groupby("spot_name").agg(
        pl.col(param).max().alias("max_energy")
    )

    return max_energy_per_spot.sort("max_energy", descending=True)[
        "spot_name"
    ].to_list()


def plot_graph(variable):
    # try:
    st.header(f"{variable} per day", divider="rainbow")
    data = st.session_state.forecast_df
    chart = (
        alt.Chart(data)
        .mark_line()
        .encode(
            x="datetime:T",
            y=f"{variable}:Q",
            color="spot_name:N",
            tooltip=[
                alt.Tooltip("date_dt:T", format="%d/%m/%Y", title="Date"),
                alt.Tooltip("time_cor:N", title="Time"),
                "energy:Q",
                "spot_name:N",
                "wave_height:Q",
                "wind_approval:N",
                "wind_status:N",
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


# except Exception:
#     pass


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


@st.cache_data(ttl="6h")
def load_forecast(urls):
    tide_scraper = TidesScraper()
    tides = tide_scraper.scrape_graph()
    start_time = time.time()
    if "windfinder" in urls[0]:
        df = multithread.scrape_multiple_requests(urls, WindFinder())
    elif "windguru" in urls[0]:
        df = multithread.scrape_multiple_browser(urls, Windguru(), tides)
        df = final_forecast_format(df).sort("datetime", descending=False)
        windguru = Windguru()
        windguru.handle_windguru_alerts(df)
        # api_token =st.secrets["TELEGRAM_API_TOKEN"]
        # chat_id = st.secrets["TELEGRAM_CHAT_ID"]
        # telegram_bot = TelegramBot(api_token, chat_id)
        # #TODO si hay mayor que tal y cual envia mensaje
        # condition = df['wave_height'] >= 1.5
        # filtered_data = df[condition]
        # result_strings = filtered_data.apply(lambda row: f"{row['spot_name']} - {row['datetime']}", axis=1)
        # # Print or save the result_strings as needed
        # for string in result_strings:
        #     telegram_bot.send_message(string)

    elif "surf-forecast" in urls[0]:
        df = multithread.scrape_multiple_requests(urls, SurfForecast(), tides)
        df = final_forecast_format(df)
        df = df.unique(maintain_order=True).sort("datetime", descending=False)
        sforecast = SurfForecast()
        sforecast.handle_sforecast_alerts(df)
    elif "surfline" in urls[0]:
        df = multithread.scrape_multiple_requests(urls, Surfline())
    elif "windy.app" in urls[0]:
        df = multithread.scrape_multiple_browser(urls, WindyApp())
    elif "wisuki" in urls[0]:
        df = multithread.scrape_multiple_requests(urls, Wisuki())
    elif "worldbeachguide" in urls[0]:
        df = multithread.scrape_multiple_requests(urls, WorldBeachGuide())
    elif "windy.com" in urls[0]:
        df = multithread.scrape_multiple_requests(urls, WindyCom())
    print("--- %s seconds ---" % (time.time() - start_time))

    return df


def custom_sort_key(item):
    custom_order = {"Hoy": 1, "Mañana": 2, "Pasado": 3, "Otro día": 4}
    return custom_order.get(item, 5)


def plot_forecast_as_table(urls):
    if "windfinder" in urls[0]:
        st.title("LANZAROTE (WINDFINDER)")
    elif "windguru" in urls[0]:
        st.title("LANZAROTE (WINDGURU)")
    elif "surf-forecast" in urls[0]:
        st.title("LANZAROTE (SURF-FORECAST)")
    elif "surfline" in urls[0]:
        st.title("LANZAROTE (SURFLINE)")
    elif "windy.app" in urls[0]:
        st.title("LANZAROTE (WINDY.APP)")
    elif "wisuki" in urls[0]:
        st.title("LANZAROTE (WISUKI)")
    elif "worldbeachguide" in urls[0]:
        st.title("LANZAROTE (WORLDBEACHGUIDE)")
    elif "windy.com" in urls[0]:
        st.title("LANZAROTE (WINDY.COM)")

    initial_forecast = load_forecast(urls)
    st.session_state.forecast_df = initial_forecast
    if st.session_state.forecast_df.is_empty():
        st.write("The DataFrame is empty.")
    else:
        date_list = list(set(st.session_state.forecast_df["date"].to_list()))
        date_name_list = list(set(st.session_state.forecast_df["date_name"].to_list()))
        wind_status_list = list(
            set(st.session_state.forecast_df["wind_status"].to_list())
        )
        all_beaches = list(set(st.session_state.forecast_df["spot_name"].to_list()))
        all_wind_approvals = list(
            set(st.session_state.forecast_df["wind_approval"].to_list())
        )

        # CREATE MULTISELECT
        date_name_selection = st.multiselect(
            "Nombre del día:", date_name_list, default=date_name_list
        )
        date_selection = st.multiselect("Fecha:", date_list, default=date_list)
        wind_status_selection = st.multiselect(
            "Estado del viento:",
            wind_status_list,
            default=wind_status_list,
        )
        selected_wave_height = plot_selected_wave_height(DEFAULT_WAVE_HEIGHT)
        selected_swell_height = plot_selected_swell_height()
        selected_wave_period = plot_selected_wave_period()
        if "surf-forecast" in urls[0]:
            selected_wave_energy = plot_selected_wave_energy()
        selected_wind_speed = plot_selected_wind_speed()

        beach_selection = st.multiselect("Playa:", all_beaches, default=all_beaches)

        wind_approval_selection = st.multiselect(
            "Aprobación del viento:",
            all_wind_approvals,
            default=get_default_wind_approval_selection(all_wind_approvals),
        )

        date_condition = st.session_state.forecast_df["date"].is_in(date_selection)
        date_name_condition = st.session_state.forecast_df["date_name"].is_in(
            date_name_selection
        )
        wind_status_condition = st.session_state.forecast_df["wind_status"].is_in(
            wind_status_selection
        )
        beach_condition = st.session_state.forecast_df["spot_name"].is_in(
            beach_selection
        )
        wind_approval_condition = st.session_state.forecast_df["wind_approval"].is_in(
            wind_approval_selection
        )
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
            ) & (
                st.session_state.forecast_df["swell_height"] <= selected_swell_height[1]
            )
        else:
            swell_height_condition = True

        if "surf-forecast" in urls[0]:
            wave_energy_condition = (
                st.session_state.forecast_df["energy"] >= selected_wave_energy[0]
            ) & (st.session_state.forecast_df["energy"] <= selected_wave_energy[1])
        else:
            wave_energy_condition = True

        # Combine conditions using bitwise AND operator
        mask = (
            date_condition
            & date_name_condition
            & wind_status_condition
            & beach_condition
            & wind_approval_condition
            & wave_height_condition
            & wave_period_condition
            & wind_speed_condition
            & swell_height_condition
            & wave_energy_condition
        )

        st.session_state.forecast_df = st.session_state.forecast_df.filter(mask)
        # st.session_state.forecast_df = st.session_state.forecast_df.with_columns(
        #     pl.col("date").str.strptime(pl.Date, format="%d/%m/%Y").cast(pl.Date)
        # )
        # st.session_state.forecast_df = st.session_state.forecast_df.with_columns(
        #     "time", pl.col("time").str.strptime(pl.Time, format="%H:%M").cast(pl.Time)
        # )
        date = st.session_state.forecast_df["datetime"].dt.date().to_list()
        time = [
            element.replace(":", "\:")
            for element in st.session_state.forecast_df["time"].to_list()
        ]
        st.session_state.forecast_df = st.session_state.forecast_df.with_columns(
            pl.Series(name="date_dt", values=date)
        )

        st.session_state.forecast_df = st.session_state.forecast_df.with_columns(
            pl.Series(name="time_cor", values=time)
        )
        if "surf-forecast" in urls[0]:
            plot_graph("energy")
        plot_graph("wave_period")

        if "surf-forecast" in urls[0]:
            grouped_data = st.session_state.forecast_df.groupby("spot_name").agg(
                pl.col("energy").max().alias("total_energy")
            )
            grouped_data = grouped_data.sort("total_energy", descending=True)
        else:
            grouped_data = st.session_state.forecast_df.groupby("spot_name").agg(
                pl.col("wave_period").max().alias("total_period")
            )
            grouped_data = grouped_data.sort("total_period", descending=True)

        with st.container():
            for i in range(len(grouped_data)):
                spot_name = grouped_data[i]["spot_name"].to_numpy()[0]
                group_df = st.session_state.forecast_df.filter(
                    pl.col("spot_name") == spot_name
                )

                st.subheader(f"Spot: {spot_name}")
                forecast_df_dropped = group_df.drop("spot_name")
                forecast_df_dropped = forecast_df_dropped.sort(
                    "datetime", descending=False
                )
                forecast_df_dropped = forecast_df_dropped.unique(
                    subset=["datetime"]
                ).drop("datetime")
                st.dataframe(forecast_df_dropped, hide_index=True)
