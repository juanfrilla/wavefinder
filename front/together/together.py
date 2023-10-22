import streamlit as st
from multi.multiprocess import scrape_multiple_sites
from utils import combine_df
import polars as pl

DEFAULT_MIN_WAVE_HEIGHT = 1.30
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
def plot_forecast_as_table(urls):

    st.session_state.forecast_df = load_forecast(urls)
    if st.session_state.forecast_df.is_empty():
        st.write("The DataFrame is empty.")
    else:
        # GET UNIQUES
        date_name_list = st.session_state.forecast_df["date"].unique().tolist()
        wind_status_list = st.session_state.forecast_df["wind_status"].unique().tolist()
        all_beaches = st.session_state.forecast_df["spot_name"].unique().tolist()
        all_wind_approvals = (
            st.session_state.forecast_df["wind_approval"].unique().tolist()
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
        selected_wave_height = plot_selected_wave_height()
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
            (st.session_state.forecast_df["date"].isin(date_name_selection))
            & (st.session_state.forecast_df["wind_status"].isin(wind_status_selection))
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

@st.cache_data(ttl=7200)
def load_forecast(_scraper_objects):
    forecast = pl.DataFrame()
    list_of_df = list(scrape_multiple_sites(_scraper_objects))
    
    for df in list_of_df:
        df = combine_df(df, forecast)

    return df