from multi.threadingresult import ThreadWithReturnValue
import utils
import polars as pl
from streamlit.runtime.scriptrunner import add_script_run_ctx
import concurrent.futures
import os


def scrape_multiple_browser(urls, _object, tides):
    arguments = [(url, tides) for url in urls]
    forecast = pl.DataFrame()
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=os.cpu_count() - 1
    ) as executor:
        results = list(executor.map(_object.scrape, arguments))

    for df in results:
        if not df.is_empty():
            forecast = utils.combine_df(forecast, df)
    return forecast


def scrape_multiple_requests(urls, _object, tides, batch_size=8):
    forecast = pl.DataFrame()
    url_batches = [urls[i : i + batch_size] for i in range(0, len(urls), batch_size)]

    for url_list in url_batches:
        threads = list()
        for url in url_list:
            x = ThreadWithReturnValue(target=_object.scrape, args=(url, tides))

            add_script_run_ctx(x)
            threads.append(x)
            x.start()

        for thread in threads:
            df = thread.join()
            if df is not None and not df.is_empty():
                df = utils.handle_wind(df)
                forecast = utils.combine_df(forecast, df)
    return forecast
