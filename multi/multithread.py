from multi.threadingresult import ThreadWithReturnValue
import utils
import pandas as pd
from streamlit.runtime.scriptrunner import add_script_run_ctx
from time import sleep
import streamlit as st

#TODO : cambiar a yields para liberar memoria
@st.cache_data(ttl=7200)
def scrape_multiple_browser(urls, _object):
    st.session_state.forecast = pd.DataFrame()
    st.session_state.results = []
    with utils.open_browser() as browser:
        for index, url in enumerate(urls):
            st.session_state.results.append(_object.scrape(browser, url, index))

    for url, content in zip(urls, st.session_state.results):
        df = utils.handle_wind(content)
        st.session_state.forecast = utils.combine_df(df, st.session_state.forecast)

    return st.session_state.forecast

@st.cache_data(ttl=7200)
def scrape_multiple_requests(urls, _object, batch_size=8):
    forecast = pd.DataFrame()
    dfs = []
    url_batches = [urls[i : i + batch_size] for i in range(0, len(urls), batch_size)]

    for url_list in url_batches:
        threads = list()
        for url in url_list:
            x = ThreadWithReturnValue(target=_object.scrape, args=(url,))

            add_script_run_ctx(x)
            threads.append(x)
            x.start()

        for thread in threads:
            df = thread.join()
            dfs.append(df)
        sleep(10)

    for df in dfs:
        df = utils.handle_wind(df)
        forecast = utils.combine_df(forecast, df)

    return forecast
