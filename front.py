import streamlit as st

import time
from utils import final_format
from multi import multithread
from scrapers.windfinder import WindFinder
from scrapers.windguru import Windguru
from scrapers.tides import TidesScraper


@st.experimental_memo(ttl=7200) #si cambio este, me quita algunos spots
def load_forecast(urls):
    start_time = time.time()
    if "windfinder" in urls[1]:
        df = multithread.scrape_multiple_requests(urls, WindFinder())
    elif "windguru" in urls[1]:
        df = multithread.scrape_multiple_browser(urls, Windguru())
    df = final_format(df)
    print("--- %s seconds ---" % (time.time() - start_time))

    return df

@st.experimental_memo(ttl=7200) #si cambio este, me quita algunos spots
def load_tides():
    start_time = time.time()
    tide_scraper = TidesScraper()
    df = tide_scraper.scrape()
    print("--- %s seconds ---" % (time.time() - start_time))

    return df


def plot_forecast(urls):
    if "windfinder" in urls[1]:
        st.title("SOUTH COAST OF LANZAROTE")
    elif "windguru" in urls[1]:
        st.title("NORTH COAST OF LANZAROTE")

    st.session_state.forecast_df = load_forecast(urls)
    if st.session_state.forecast_df.empty:
        st.write("The DataFrame is empty.")
    else:
        # GET UNIQUES
        date_name = st.session_state.forecast_df["date"].unique().tolist()
        wind_state = st.session_state.forecast_df["wind_status"].unique().tolist()
        default_wind_state = ["Cross-off"] if "Offshore" not in wind_state else ["Offshore"]
        all_beaches = st.session_state.forecast_df["spot_name"].unique().tolist()

        approval = st.session_state.forecast_df["approval"].unique().tolist()
        # tides_state = st.session_state.forecast_df["tide_state"].unique().tolist()
        # island = st.session_state.forecast_df["island"].unique().tolist()

        # CREATE MULTISELECT
        date_name_selection = st.multiselect("Fecha:", date_name, default=date_name)
        wind_state_selection = st.multiselect(
            "Estado del viento:", wind_state, default=default_wind_state
        )

        beach_selection = st.multiselect("Playa:", all_beaches, default=all_beaches)

        approval_selection = st.multiselect("Valoración:", approval, default=approval)

        # tides_state_selection = st.multiselect(
        #     "Estado de la marea:", tides_state, default=tides_state
        # )
        # --- FILTER DATAFRAME BASED ON SELECTION
        mask = (
            (st.session_state.forecast_df["date"].isin(date_name_selection))
            & (st.session_state.forecast_df["wind_status"].isin(wind_state_selection))
            & (st.session_state.forecast_df["spot_name"].isin(beach_selection))
            & (st.session_state.forecast_df["approval"].isin(approval_selection))
            # & (st.session_state.forecast_df["tide_state"].isin(tides_state_selection))
        )

        # --- GROUP DATAFRAME AFTER SELECTION
        st.session_state.forecast_df = st.session_state.forecast_df[mask]

        with st.container():
            # st.dataframe(st.session_state.forecast_df, height=500, width=800)
            st.dataframe(
                st.session_state.forecast_df.style.set_properties(
                    **{"overflow-y": "auto", "overflow-x": "auto"}
                )
            )

def plot_tides():
    st.session_state.tides_df = load_tides()
    st.write("Tabla de mareas")
    st.table(st.session_state.tides_df)
