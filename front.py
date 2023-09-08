import streamlit as st

import time
from utils import final_format
from multi import multithread
from scrapers.windfinder import WindFinder
from scrapers.windguru import Windguru
from scrapers.sforecast import SurfForecast
from scrapers.tides import TidesScraper

DEFAULT_MIN_WAVE_HEIGHT = 1.30
DEFAULT_MIN_WAVE_PERIOD = 7


def get_default_approval_list(approval_list):
    if "No Favorable" in approval_list and "Favorable" in approval_list:
        return ["Favorable"]
    elif "Favorable" in approval_list:
        return ["Favorable"]
    return []


def get_default_wind_status_list(wind_status_list):
    if "Cross-off" in wind_status_list and "Offshore" in wind_status_list:
        return ["Cross-off", "Offshore"]
    elif "Offshore" in wind_status_list:
        return ["Offshore"]
    elif "Cross-off" in wind_status_list:
        return ["Cross-off"]
    return []


def plot_selected_wave_height():
    min_wave_height = float(st.session_state.forecast_df["wave_height"].min())
    max_wave_height = float(st.session_state.forecast_df["wave_height"].max())
    if max_wave_height < DEFAULT_MIN_WAVE_HEIGHT:
        default_wave_height_selection = (1.0, DEFAULT_MIN_WAVE_HEIGHT)
    else:
        default_wave_height_selection = (DEFAULT_MIN_WAVE_HEIGHT, max_wave_height)
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


@st.experimental_memo(ttl=7200)  # si cambio este, me quita algunos spots
def load_forecast(urls):
    start_time = time.time()
    if "windfinder" in urls[1]:
        df = multithread.scrape_multiple_requests(urls, WindFinder())
    elif "windguru" in urls[1]:
        df = multithread.scrape_multiple_browser(urls, Windguru())
    elif "surf-forecast" in urls[1]:
        df = multithread.scrape_multiple_requests(urls, SurfForecast())
    df = final_format(df)
    print("--- %s seconds ---" % (time.time() - start_time))

    return df


@st.experimental_memo(ttl=7200)  # si cambio este, me quita algunos spots
def load_tides():
    start_time = time.time()
    tide_scraper = TidesScraper()
    df = tide_scraper.scrape()
    print("--- %s seconds ---" % (time.time() - start_time))

    return df


def plot_forecast(urls):
    if "windfinder" in urls[1]:
        st.title("SOUTH COAST OF LANZAROTE")
    elif "windguru" or "surf-forecast" in urls[1]:
        st.title("NORTH COAST OF LANZAROTE")

    st.session_state.forecast_df = load_forecast(urls)
    if st.session_state.forecast_df.empty:
        st.write("The DataFrame is empty.")
    else:
        # GET UNIQUES
        date_name_list = st.session_state.forecast_df["date"].unique().tolist()
        wind_status_list = st.session_state.forecast_df["wind_status"].unique().tolist()

        all_beaches = st.session_state.forecast_df["spot_name"].unique().tolist()

        approval_list = st.session_state.forecast_df["approval"].unique().tolist()

        selected_wave_height = plot_selected_wave_height()
        selected_wave_period = plot_selected_wave_period()

        # CREATE MULTISELECT
        date_name_selection = st.multiselect(
            "Fecha:", date_name_list, default=date_name_list
        )
        wind_status_selection = st.multiselect(
            "Estado del viento:",
            wind_status_list,
            default=get_default_wind_status_list(wind_status_list),
        )

        beach_selection = st.multiselect("Playa:", all_beaches, default=all_beaches)

        approval_selection = st.multiselect(
            "Valoración:",
            approval_list,
            default=get_default_approval_list(approval_list),
        )

        # tides_state_selection = st.multiselect(
        #     "Estado de la marea:", tides_state, default=tides_state
        # )
        # --- FILTER DATAFRAME BASED ON SELECTION
        mask = (
            (st.session_state.forecast_df["date"].isin(date_name_selection))
            & (st.session_state.forecast_df["wind_status"].isin(wind_status_selection))
            & (st.session_state.forecast_df["spot_name"].isin(beach_selection))
            & (st.session_state.forecast_df["approval"].isin(approval_selection))
            & (st.session_state.forecast_df["wave_height"] >= selected_wave_height[0])
            & (st.session_state.forecast_df["wave_height"] <= selected_wave_height[1])
            & (st.session_state.forecast_df["wave_period"] >= selected_wave_period[0])
            & (st.session_state.forecast_df["wave_period"] <= selected_wave_period[1])
            # & (st.session_state.forecast_df["tide_state"].isin(tides_state_selection))
        )

        # --- GROUP DATAFRAME AFTER SELECTION
        st.session_state.forecast_df = st.session_state.forecast_df[mask]

        grouped_data = st.session_state.forecast_df.groupby("spot_name")

        # Display tables for each group
        with st.container():
            for spot_name, group_df in grouped_data:
                st.subheader(f"Spot: {spot_name}")

                # Drop the "spot_name" column from the group DataFrame
                group_df = group_df.drop(columns=["spot_name"])

                st.dataframe(
                    group_df.style.set_properties(
                        **{"overflow-y": "auto", "overflow-x": "auto"}
                    ),
                    hide_index=True,
                )


def plot_tides():
    st.session_state.tides_df = load_tides()
    st.subheader("Tabla de mareas")
    st.dataframe(st.session_state.tides_df, hide_index=True)
