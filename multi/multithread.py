from multi.threadingresult import ThreadWithReturnValue
import multiprocessing
import utils
import pandas as pd
from streamlit.runtime.scriptrunner import add_script_run_ctx

def scrape_multiple_browser(urls, object):
    num_processes = 3
    forecast = pd.DataFrame()

    with multiprocessing.Pool(processes=num_processes) as pool:
        scraper_objects = []
        for url in urls:
            object.url=url
            scraper_objects.append(object)
        results = pool.map(object.scrape, scraper_objects)

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
