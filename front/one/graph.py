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


# DEFAULT_MIN_WAVE_HEIGHT = 1.30
DEFAULT_MIN_WAVE_HEIGHT = 1.0
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


@st.cache_data(ttl=7200)
def load_forecast(urls):
    start_time = time.time()
    if "windfinder" in urls[0]:
        df = multithread.scrape_multiple_requests(urls, WindFinder())
    elif "windguru" in urls[0]:
        df = multithread.scrape_multiple_browser(urls, Windguru())
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


@st.cache_data(ttl=7200)
def load_tides():
    start_time = time.time()
    tide_scraper = TidesScraper()
    df = tide_scraper.scrape_table()
    print("--- %s seconds ---" % (time.time() - start_time))

    return df


def plot_forecast_as_graph(urls):
    if "windfinder" in urls[0]:
        st.title("SOUTH COAST OF LANZAROTE (WINDFINDER)")
    elif "windguru" in urls[0]:
        st.title("NORTH COAST OF LANZAROTE (WINDGURU)")
    elif "surf-forecast" in urls[0]:
        st.title("NORTH COAST OF LANZAROTE (SURF-FORECAST)")
    elif "surfline" in urls[0]:
        st.title("NORTH AND SOUTH COAST OF LANZAROTE (SURFLINE)")
    elif "windy.app" in urls[0]:
        st.title("NORTH AND SOUTH COAST OF LANZAROTE (WINDY.APP)")
    elif "wisuki" in urls[0]:
        st.title("NORTH AND SOUTH COAST OF LANZAROTE (WISUKI)")
    elif "worldbeachguide" in urls[0]:
        st.title("SOUTH COAST OF LANZAROTE (WORLDBEACHGUIDE)")

    st.session_state.forecast_df = load_forecast(urls)
    if st.session_state.forecast_df.empty:
        st.write("The DataFrame is empty.")
    else:
        all_beaches = st.session_state.forecast_df["spot_name"].unique().tolist()
        # all_graphs = ["wave_height", "wind_status", "wind_speed", "wave_period", "tides"]
        # graph_selection = st.multiselect("Gráficas:", all_graphs, default=all_graphs)
        beach_selection = st.multiselect("Playa:", all_beaches, default=all_beaches)
        mask = st.session_state.forecast_df["spot_name"].isin(beach_selection)
        st.session_state.forecast_df = st.session_state.forecast_df[mask]

        try:
            st.header("Altura por día", divider="rainbow")
            st.line_chart(
                st.session_state.forecast_df,
                x="datetime",
                y="wave_height",
                color="spot_name",
            )
        except:
            pass
        try:
            st.header("Estado del viento por día", divider="rainbow")
            st.bar_chart(
                st.session_state.forecast_df,
                x="datetime",
                y="spot_name",
                color="wind_status",
            )
        except:
            pass

        try:
            st.header("Velocidad del viento por día", divider="rainbow")
            st.line_chart(
                st.session_state.forecast_df,
                x="datetime",
                y="wind_speed",
                color="spot_name",
            )
        except:
            pass

        try:
            st.header("Periodo de las olas por día", divider="rainbow")
            st.line_chart(
                st.session_state.forecast_df,
                x="datetime",
                y="wave_period",
                color="spot_name",
            )
        except:
            pass

        st.session_state.tides_df = load_tides()
        st.subheader("Tabla de mareas")
        st.dataframe(st.session_state.tides_df, hide_index=True)
