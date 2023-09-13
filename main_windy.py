#from front import plot_forecast, plot_tides

from utils import open_browser
from scrapers.windy import Windy

# if __name__ == "__main__":
#     urls = [
#         "https://windy.app/forecast2/spot/647997/Faro+de+Pechiguera"
#     ]
    
#     plot_forecast(urls)
#     plot_tides()

if __name__ == "__main__":
    windy = Windy()
    with open_browser() as browser:
        soup = windy.scrape(browser, "https://windy.app/forecast2/spot/647997/Faro+de+Pechiguera")