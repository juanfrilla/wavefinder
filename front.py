import streamlit as st

import time
from utils import *
from multi import multithread
from scrapers.windfinder import WindFinder
from scrapers.windguru import Windguru


@st.experimental_memo(ttl=7200) #si cambio este, me quita algunos spots
def load_data(urls):
    start_time = time.time()
    if "windfinder" in urls[1]:
        df = multithread.scrape_multiple_requests(urls, WindFinder())
    elif "windguru" in urls[1]:
        df = multithread.scrape_multiple_browser(urls, Windguru())
    df = final_format(df)
    print("--- %s seconds ---" % (time.time() - start_time))

    return df


def plot_data(urls):
    if "windfinder" in urls[1]:
        st.title("SOUTH COAST OF LANZAROTE")
    elif "windguru" in urls[1]:
        st.title("NORTH COAST OF LANZAROTE")

    st.session_state.df = load_data(urls)
    if st.session_state.df.empty:
        st.write("The DataFrame is empty.")
    else:
        # GET UNIQUES
        date_name = st.session_state.df["date"].unique().tolist()
        wind_state = st.session_state.df["wind_status"].unique().tolist()
        default_wind_state = ["Cross-off"] if "Offshore" not in wind_state else ["Offshore"]
        all_beaches = st.session_state.df["spot_name"].unique().tolist()
        # lg_beaches = (
        #     st.session_state.df.loc[st.session_state.df["island"] == "La Graciosa", "beach"]
        #     .unique()
        #     .tolist()
        # )
        # lz_beaches = (
        #     st.session_state.df.loc[st.session_state.df["island"] == "Lanzarote", "beach"]
        #     .unique()
        #     .tolist()
        # )
        # gc_beaches = (
        #     st.session_state.df.loc[
        #         st.session_state.df["island"] == "Gran Canaria", "beach"
        #     ]
        #     .unique()
        #     .tolist()
        # )

        approval = st.session_state.df["approval"].unique().tolist()
        # tides_state = st.session_state.df["tide_state"].unique().tolist()
        # island = st.session_state.df["island"].unique().tolist()

        # CREATE MULTISELECT
        date_name_selection = st.multiselect("Fecha:", date_name, default=date_name)
        wind_state_selection = st.multiselect(
            "Estado del viento:", wind_state, default=default_wind_state
        )

        # island_selection = st.multiselect("Isla:", island, default=["Lanzarote"])

        # if island_selection == ["La Graciosa"]:
        #     beach_selection = st.multiselect("Playa:", lg_beaches, default=lg_beaches)
        # if island_selection == ["Lanzarote"]:
        #     beach_selection = st.multiselect("Playa:", lz_beaches, default=lz_beaches)
        # elif island_selection == ["Gran Canaria"]:
        #     beach_selection = st.multiselect("Playa:", gc_beaches, default=gc_beaches)
        # else:
        #     beach_selection = st.multiselect("Playa:", all_beaches, default=all_beaches)

        beach_selection = st.multiselect("Playa:", all_beaches, default=all_beaches)

        approval_selection = st.multiselect("Valoración:", approval, default=approval)
        # all_page_ratings = st.session_state.df["page_rating"].unique().tolist()
        # page_rating_selection = st.multiselect(
        #     "Valoración de la página:", all_page_ratings, default=all_page_ratings
        # )

        # tides_state_selection = st.multiselect(
        #     "Estado de la marea:", tides_state, default=tides_state
        # )
        # --- FILTER DATAFRAME BASED ON SELECTION
        mask = (
            (st.session_state.df["date"].isin(date_name_selection))
            & (st.session_state.df["wind_status"].isin(wind_state_selection))
            & (st.session_state.df["spot_name"].isin(beach_selection))
            & (st.session_state.df["approval"].isin(approval_selection))
            # & (st.session_state.df["tide_state"].isin(tides_state_selection))
            # & (st.session_state.df["page_rating"].isin(page_rating_selection))
        )

        # --- GROUP DATAFRAME AFTER SELECTION
        st.session_state.df = st.session_state.df[mask]

        with st.container():
            # st.dataframe(st.session_state.df, height=500, width=800)
            st.dataframe(
                st.session_state.df.style.set_properties(
                    **{"overflow-y": "auto", "overflow-x": "auto"}
                )
            )
