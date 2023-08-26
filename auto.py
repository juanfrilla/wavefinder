from scrapers.windfinder import WindFinder
from utils import *
if __name__ == "__main__":
    filename="./samples/costa_teguise.html"
    windfinder = WindFinder()
    soup = windfinder.beach_request(windfinder.COSTA_TEGUISE_URL)
    export_to_html(filename, soup)