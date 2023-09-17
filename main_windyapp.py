from front.one import plot_forecast, plot_tides
from urls.windyapp import WINDYAPP_URLS

if __name__ == "__main__":
    plot_forecast(WINDYAPP_URLS)
    plot_tides()
