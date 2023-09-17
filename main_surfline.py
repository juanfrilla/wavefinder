import warnings

warnings.filterwarnings("ignore")
from front.one import plot_forecast, plot_tides
from urls.surfline import SURFLINE_URLS


def main():

    plot_forecast(SURFLINE_URLS)
    plot_tides()


if __name__ == "__main__":
    main()
