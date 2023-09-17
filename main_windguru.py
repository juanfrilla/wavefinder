from front.one import plot_forecast, plot_tides
from urls.windguru import WINDGURU_URLS

if __name__ == "__main__":
    plot_forecast(WINDGURU_URLS)
    plot_tides()
