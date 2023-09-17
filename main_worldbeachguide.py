from front.one import plot_forecast, plot_tides
from urls.worldbeachguide import WORLDBEACHGUIDE_URLS

if __name__ == "__main__":
    plot_forecast(WORLDBEACHGUIDE_URLS)
    plot_tides()
