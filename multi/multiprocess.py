import multiprocessing
from multi.multithread import scrape_multiple_browser, scrape_multiple_requests


def scrape_multiple_browser_process(urls, object, return_list):
    forecast = scrape_multiple_browser(urls, object)
    return_list.append(forecast)
    return return_list


def scrape_multiple_requests_process(urls, object, return_list):
    forecast = scrape_multiple_requests(urls, object)
    return_list.append(forecast)
    return return_list


def scrape_multiple_sites(scraper_objects: list):
    processes = []
    manager = multiprocessing.Manager()
    return_list = manager.list()
    for scraper_object in scraper_objects:
        process = multiprocessing.Process(
            target=scraper_object["target"],
            args=(scraper_object["urls"], scraper_object["object"], return_list),
        )
        processes.append(process)
        process.start()

    # Wait for all processes to finish
    for process in processes:
        process.join()
    return return_list
