from multi.threadingresult import ThreadWithReturnValue
import multiprocessing
import utils
import pandas as pd
from streamlit.runtime.scriptrunner import add_script_run_ctx


def scrape_multiple_browser(urls, object):
    forecast = pd.DataFrame()

    results = []
    for url in urls:
        results.append(object.scrape(url))

    for url, content in zip(urls, results):
        forecast = utils.combine_df(forecast, content)

    return forecast


def scrape_multiple_requests(urls, object):
    threads = list()

    forecast = pd.DataFrame()

    for url in urls:
        x = ThreadWithReturnValue(target=object.scrape, args=(url,))

        add_script_run_ctx(x)
        threads.append(x)
        x.start()

    for thread in threads:
        df = thread.join()
        forecast = utils.combine_df(forecast, df)

    return forecast
