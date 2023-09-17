from front.one import plot_forecast, plot_tides
from urls.wisuki import WISUKI_URLS

if __name__ == "__main__":
    plot_forecast(WISUKI_URLS)
    plot_tides()
