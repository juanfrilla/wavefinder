from front.one import plot_forecast, plot_tides
from urls.windfinder import WINDFINDER_URLS

if __name__ == "__main__":
    plot_forecast(WINDFINDER_URLS)
    plot_tides()
