from front.one import plot_forecast, plot_tides
from urls.sforecast import SFORECAST_URLS

if __name__ == "__main__":
    plot_forecast(SFORECAST_URLS)
    plot_tides()
