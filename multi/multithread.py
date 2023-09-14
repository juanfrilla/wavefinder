from multi.threadingresult import ThreadWithReturnValue
import utils
import pandas as pd
from streamlit.runtime.scriptrunner import add_script_run_ctx
from time import sleep


def scrape_multiple_browser(urls, object):
    forecast = pd.DataFrame()
    results = []
    with utils.open_browser() as browser:
        for url in urls:
            results.append(object.scrape(browser, url))

        for url, content in zip(urls, results):
            df = utils.handle_wind(content)
            forecast = utils.combine_df(df, forecast)

    return forecast


def scrape_multiple_requests(urls, object, batch_size=8):
    forecast = pd.DataFrame()
    dfs = []
    # Create batches of URLs to scrape
    url_batches = [urls[i : i + batch_size] for i in range(0, len(urls), batch_size)]

    for url_list in url_batches:
        threads = list()
        for url in url_list:
            x = ThreadWithReturnValue(target=object.scrape, args=(url,))

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


# def scrape_multiple_requests(urls, object, batch_size=8):
#     forecast = pd.DataFrame()
#     threads = []

#     # Create batches of URLs to scrape
#     url_batches = [urls[i:i + batch_size] for i in range(0, len(urls), batch_size)]

#     for batch in url_batches:
#         batch_threads = []

#         for url in batch:
#             x = Thread(target=object.scrape, args=(url,))
#             threads.append(x)
#             batch_threads.append(x)
#             x.start()

#         for thread in batch_threads:
#             thread.join()

#         batch_results = [thread.result for thread in batch_threads if hasattr(thread, 'result')]
#         if batch_results:
#             batch_df = pd.concat(batch_results, ignore_index=True)
#             forecast = utils.combine_df(forecast, batch_df)

#     return forecast
