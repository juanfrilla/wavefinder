from front import plot_forecast, plot_tides

if __name__ == "__main__":
    urls = [
        "https://www.surf-forecast.com/breaks/Arrieta/forecasts/latest/six_day",
        "https://www.surf-forecast.com/breaks/Caletade-Cabello/forecasts/latest/six_day",
        "https://www.surf-forecast.com/breaks/Jameosdel-Agua/forecasts/latest/six_day",
        "https://www.surf-forecast.com/breaks/La-Santa-The-Slab/forecasts/latest/six_day",
        "https://www.surf-forecast.com/breaks/Playade-Famara_1/forecasts/latest/six_day",
        "https://www.surf-forecast.com/breaks/San-Juan/forecasts/latest/six_day",
    ]

    plot_forecast(urls)
    plot_tides()