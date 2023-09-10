from scrapers.windfinder import WindFinder
from utils import  export_to_html
if __name__ == "__main__":
    filename="./samples/papagayo.html"
    windfinder = WindFinder()
    response = windfinder.beach_request("https://es.windfinder.com/forecast/la_palma1")
    export_to_html(filename, response)