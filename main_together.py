from multi import multiprocess

from scrapers.windfinder import WindFinder
from scrapers.windguru import Windguru
from scrapers.sforecast import SurfForecast
from scrapers.surfline import Surfline
from scrapers.windyapp import WindyApp
from scrapers.wisuki import Wisuki
from scrapers.worldbeachguide import WorldBeachGuide

from urls.sforecast import SFORECAST_URLS
from urls.surfline import SURFLINE_URLS
from urls.windfinder import WINDFINDER_URLS
from urls.windguru import WINDGURU_URLS
from urls.wisuki import WISUKI_URLS
from urls.windyapp import WINDYAPP_URLS



scraper_objects = [
    # {
    #     "object": WindFinder(),
    #     "target": multiprocess.scrape_multiple_requests_process,
    #     "urls": WINDFINDER_URLS,
    # },
    # {
    #     "object": Windguru(),
    #     "target": multiprocess.scrape_multiple_browser_process,
    #     "urls": WINDGURU_URLS,
    # },
    {
        "object": SurfForecast(),
        "target": multiprocess.scrape_multiple_requests_process,
        "urls": SFORECAST_URLS,
    },
    # {
    #     "object": Surfline(),
    #     "target": multiprocess.scrape_multiple_requests_process,
    #     "urls": SURFLINE_URLS,
    # },
    {
        "object": Wisuki(),
        "target": multiprocess.scrape_multiple_requests_process,
        "urls": WISUKI_URLS,
    },
    {
        "object": WindyApp(),
        "target": multiprocess.scrape_multiple_browser_process,
        "urls": WINDYAPP_URLS,
    },
]
if __name__ == "__main__":
    df = multiprocess.scrape_multiple_sites(scraper_objects)
    
    dfie = list(df)
    
    print()
