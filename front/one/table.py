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
from APIS.telegram_api import TelegramBot
import altair as alt
import polars as pl

DEFAULT_MIN_WAVE_PERIOD = 7


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


@st.experimental_memo(ttl="1h")
def load_forecast(urls):
    start_time = time.time()
    if "windfinder" in urls[0]:
        df = multithread.scrape_multiple_requests(urls, WindFinder())
    elif "windguru" in urls[0]:
        df = multithread.scrape_multiple_browser(urls, Windguru())
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
        df = multithread.scrape_multiple_requests(urls, SurfForecast())
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
    df = final_forecast_format(df)
    print("--- %s seconds ---" % (time.time() - start_time))

    return df


@st.experimental_memo(ttl="23h")
def load_tides():
    start_time = time.time()
    tide_scraper = TidesScraper()
    df = tide_scraper.scrape_table()
    print("--- %s seconds ---" % (time.time() - start_time))

    return df


def plot_forecast_as_table(urls):
    if "windfinder" in urls[0]:
        default_wave_height = 3.0
        st.title("LANZAROTE (WINDFINDER)")
    elif "windguru" in urls[0]:
        default_wave_height = 3.0
        st.title("LANZAROTE (WINDGURU)")
    elif "surf-forecast" in urls[0]:
        default_wave_height = 1.0
        st.title("LANZAROTE (SURF-FORECAST)")
    elif "surfline" in urls[0]:
        default_wave_height = 3.0
        st.title("LANZAROTE (SURFLINE)")
    elif "windy.app" in urls[0]:
        default_wave_height = 3.0
        st.title("LANZAROTE (WINDY.APP)")
    elif "wisuki" in urls[0]:
        default_wave_height = 3.0
        st.title("LANZAROTE (WISUKI)")
    elif "worldbeachguide" in urls[0]:
        default_wave_height = 3.0
        st.title("LANZAROTE (WORLDBEACHGUIDE)")
    elif "windy.com" in urls[0]:
        default_wave_height = 1.0
        st.title("LANZAROTE (WINDY.COM)")

    initial_forecast = load_forecast(urls)
    st.session_state.forecast_df = initial_forecast
    if st.session_state.forecast_df.is_empty():
        st.write("The DataFrame is empty.")
    else:
        # GET UNIQUES
        date_name_list = (
            st.session_state.forecast_df.to_pandas()["date_name"].unique().tolist()
        )
        wind_status_list = (
            st.session_state.forecast_df.to_pandas()["wind_status"].unique().tolist()
        )
        all_beaches = (
            st.session_state.forecast_df.to_pandas()["spot_name"].unique().tolist()
        )
        all_wind_approvals = (
            st.session_state.forecast_df.to_pandas()["wind_approval"].unique().tolist()
        )

        # CREATE MULTISELECT
        date_name_selection = st.multiselect(
            "Fecha:", date_name_list, default=date_name_list
        )
        wind_status_selection = st.multiselect(
            "Estado del viento:",
            wind_status_list,
            default=wind_status_list,
        )
        selected_wave_height = plot_selected_wave_height(default_wave_height)
        selected_wave_period = plot_selected_wave_period()
        selected_wind_speed = plot_selected_wind_speed()

        beach_selection = st.multiselect("Playa:", all_beaches, default=all_beaches)

        wind_approval_selection = st.multiselect(
            "Aprobación del viento:",
            all_wind_approvals,
            default=get_default_wind_approval_selection(all_wind_approvals),
        )

        # tides_state_selection = st.multiselect(
        #     "Estado de la marea:", tides_state, default=tides_state
        # )
        # --- FILTER DATAFRAME BASED ON SELECTION

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
        # tide_state_condition = forecast_df['tide_state'].is_in(tides_state_selection)  # Uncomment this line if you want to include this condition

        # Combine conditions using bitwise AND operator
        mask = (
            date_name_condition
            & wind_status_condition
            & beach_condition
            & wind_approval_condition
            & wave_height_condition
            & wave_period_condition
            & wind_speed_condition
        )

        # # Filter the DataFrame
        # forecast_df = forecast_df.filter(mask)

        # mask = (
        #     (pl.col("date_name").is_in(date_name_selection))
        #     & (pl.col("wind_status").is_in(wind_status_selection))
        #     & (pl.col("spot_name").is_in(beach_selection))
        #     & (pl.col("wind_approval").is_in(wind_approval_selection))
        #     & (pl.col("wave_height") >= selected_wave_height[0])
        #     & (pl.col("wave_height") <= selected_wave_height[1])
        #     & (pl.col("wave_period") >= selected_wave_period[0])
        #     & (pl.col("wave_period") <= selected_wave_period[1])
        #     & (pl.col("wind_speed") >= selected_wind_speed[0])
        #     & (pl.col("wind_speed") <= selected_wind_speed[1])
        # )

        # --- GROUP DATAFRAME AFTER SELECTION
        st.session_state.forecast_df = st.session_state.forecast_df.filter(mask)

        # try:
        st.header("Altura por día", divider="rainbow")
        data = st.session_state.forecast_df
        chart = (
            alt.Chart(data)
            .mark_line()
            .encode(
                x="datetime:T",
                y="wave_height:Q",
                color="spot_name:N",
                tooltip=[
                    alt.Tooltip("datetime:T", format="%d/%m/%Y", title="Date"),
                    alt.Tooltip("datetime:T", format="%H:%M", title="Time"),
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

        # grouped_data = st.session_state.forecast_df.groupby("spot_name")
        with st.container():
            grouped_data = st.session_state.forecast_df.groupby("spot_name")
            for spot_name, group_df in grouped_data:
                st.subheader(f"Spot: {spot_name}")
                # group_df = group_df.drop_in_place("spot_name")

                st.dataframe(group_df.to_pandas(), hide_index=True)

        # Display tide data
        st.session_state.tides_df = load_tides()
        st.subheader("Tabla de mareas")
        st.dataframe(st.session_state.tides_df, hide_index=True)
