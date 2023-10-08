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
from scrapers.worldbeachguide import WorldBeachGuide
from scrapers.tides import TidesScraper
from APIS.telegram_api import TelegramBot
import altair as alt
import pandas as pd

# DEFAULT_MIN_WAVE_HEIGHT = 1.30
# DEFAULT_MIN_WAVE_HEIGHT = 1.0
DEFAULT_MIN_WAVE_PERIOD = 7


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


@st.cache_data(ttl="1h")
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
    df = final_forecast_format(df)
    print("--- %s seconds ---" % (time.time() - start_time))

    return df


def load_tides():
    start_time = time.time()
    tide_scraper = TidesScraper()
    df = tide_scraper.scrape_table()
    print("--- %s seconds ---" % (time.time() - start_time))

    return df


def plot_forecast_as_table(urls):
    if "windfinder" in urls[0]:
        default_wave_height = 1.50
        st.title("SOUTH COAST OF LANZAROTE (WINDFINDER)")
    elif "windguru" in urls[0]:
        default_wave_height = 1.0
        st.title("SPOTS DE SURF LANZAROTE (WINDGURU)")
    elif "surf-forecast" in urls[0]:
        default_wave_height = 1.0
        st.title("NORTH COAST OF LANZAROTE (SURF-FORECAST)")
    elif "surfline" in urls[0]:
        default_wave_height = 1.50
        st.title("NORTH AND SOUTH COAST OF LANZAROTE (SURFLINE)")
    elif "windy.app" in urls[0]:
        default_wave_height = 1.50
        st.title("NORTH AND SOUTH COAST OF LANZAROTE (WINDY.APP)")
    elif "wisuki" in urls[0]:
        default_wave_height = 1.50
        st.title("NORTH AND SOUTH COAST OF LANZAROTE (WISUKI)")
    elif "worldbeachguide" in urls[0]:
        default_wave_height = 1.50
        st.title("SOUTH COAST OF LANZAROTE (WORLDBEACHGUIDE)")

    initial_forecast = load_forecast(urls)
    st.session_state.forecast_df = initial_forecast
    st.session_state.forecast_graph = initial_forecast
    if st.session_state.forecast_df.empty:
        st.write("The DataFrame is empty.")
    else:
        # GET UNIQUES
        # date_name_list = st.session_state.forecast_df["datetime"].unique().tolist()
        wind_status_list = st.session_state.forecast_df["wind_status"].unique().tolist()
        all_beaches = st.session_state.forecast_df["spot_name"].unique().tolist()
        all_wind_approvals = (
            st.session_state.forecast_df["wind_approval"].unique().tolist()
        )

        # CREATE MULTISELECT
        # date_name_selection = st.multiselect(
        #     "Fecha:", date_name_list, default=date_name_list
        # )
        wind_status_selection = st.multiselect(
            "Estado del viento:",
            wind_status_list,
            default=wind_status_list,
        )
        selected_wave_height = plot_selected_wave_height(default_wave_height)
        selected_wave_period = plot_selected_wave_period()

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
        mask = (
            # (st.session_state.forecast_df["datetime"].isin(date_name_selection))
            (st.session_state.forecast_df["wind_status"].isin(wind_status_selection))
            & (st.session_state.forecast_df["spot_name"].isin(beach_selection))
            & (
                st.session_state.forecast_df["wind_approval"].isin(
                    wind_approval_selection
                )
            )
            & (st.session_state.forecast_df["wave_height"] >= selected_wave_height[0])
            & (st.session_state.forecast_df["wave_height"] <= selected_wave_height[1])
            & (st.session_state.forecast_df["wave_period"] >= selected_wave_period[0])
            & (st.session_state.forecast_df["wave_period"] <= selected_wave_period[1])
            # & (st.session_state.forecast_df["tide_state"].isin(tides_state_selection))
        )

        # --- GROUP DATAFRAME AFTER SELECTION
        st.session_state.forecast_df = st.session_state.forecast_df[mask]

        mask_graph = st.session_state.forecast_graph["spot_name"].isin(beach_selection)
        st.session_state.forecast_graph = st.session_state.forecast_graph[mask_graph]

        # # Extract date and time components
        # st.session_state.forecast_df['date'] = st.session_state.forecast_df['datetime'].dt.date
        # st.session_state.forecast_df['time'] = st.session_state.forecast_df['datetime'].dt.time

        try:
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
                        "datetime:T",
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

        except Exception as e:
            st.write("An error occurred:", e)

        try:
            st.header("Aprobación del viento por día", divider="rainbow")
            chart = (
                alt.Chart(st.session_state.forecast_df)
                .mark_bar()
                .encode(
                    x="datetime",
                    y="spot_name",
                    color="wind_approval:N",
                )
            )
            st.altair_chart(chart, use_container_width=True)
        except:
            pass

        try:
            st.header("Estado del viento por día", divider="rainbow")
            chart = (
                alt.Chart(st.session_state.forecast_df)
                .mark_bar()
                .encode(
                    x="datetime",
                    y="spot_name",
                    color="wind_status:N",
                )
            )
            st.altair_chart(chart, use_container_width=True)
        except:
            pass

        try:
            st.header("Dirección del viento por día", divider="rainbow")
            chart = (
                alt.Chart(st.session_state.forecast_df)
                .mark_bar()
                .encode(
                    x="datetime",
                    y="spot_name",
                    color="wind_direction:N",
                )
            )
            st.altair_chart(chart, use_container_width=True)
        except:
            pass

        grouped_data = st.session_state.forecast_df.groupby("spot_name")
        with st.container():
            for spot_name, group_df in grouped_data:
                st.subheader(f"Spot: {spot_name}")
                group_df = group_df.drop(columns=["spot_name"])

                st.dataframe(
                    group_df.style.set_properties(
                        **{"overflow-y": "auto", "overflow-x": "auto"}
                    ),
                    hide_index=True,
                )

        st.session_state.tides_df = load_tides()
        st.subheader("Tabla de mareas")
        st.dataframe(st.session_state.tides_df, hide_index=True)
