from front import plot_forecast, plot_tides

if __name__ == "__main__":
    urls = [
        "https://www.windguru.cz/586104",  # costa teguise
        "https://www.windguru.cz/49326",  # Jameos del agua
        "https://www.windguru.cz/49325",  # La garita
        "https://www.windguru.cz/49328",  # famara
    ]

    plot_forecast(urls)
    plot_tides()
