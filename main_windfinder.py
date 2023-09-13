from front import plot_forecast, plot_tides

if __name__ == "__main__":
    urls = [
        "https://es.windfinder.com/forecast/marina_rubicon_canary_islands_spain",
        "https://es.windfinder.com/forecast/playa_blanca_canary_islands_spain_marina",
        "https://es.windfinder.com/forecast/punta-pechiguera-playa-blanca",
        "https://es.windfinder.com/forecast/lanzarote_puerto_del_carmen_costa_teguis",
        "https://es.windfinder.com/forecast/lanzarote_playa_honda_costa_teguise",
    ]

    plot_forecast(urls)
    plot_tides()
