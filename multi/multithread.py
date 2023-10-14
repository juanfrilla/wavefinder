from multi.threadingresult import ThreadWithReturnValue
import utils
import pandas as pd
from streamlit.runtime.scriptrunner import add_script_run_ctx
from time import sleep


# TODO : cambiar a yields para liberar memoria
def scrape_multiple_browser(urls, _object):
    forecast = pd.DataFrame()
    results = []
    try:
        browser = utils.open_browser()
        for index, url in enumerate(urls):
            result = _object.scrape(browser, url, index)
            results.append(result)
    finally:
        browser.close()
        browser.quit()
    assert len(results) == len(urls)
    assert all(not df.empty for df in results)
    for url, content in zip(urls, results):
        df = utils.handle_wind(content)
        if not df.empty:
            forecast = utils.combine_df(df, forecast)

    return forecast


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
