from front import plot_forecast, plot_tides

if __name__ == "__main__":
    urls = [
        "https://es.wisuki.com/forecast/2843/playa-dorada",
        # "https://es.wisuki.com/forecast/6080/la-santa",
        # "https://es.wisuki.com/forecast/6269/caleta-caballo",
        # "https://es.wisuki.com/forecast/2833/famara",
        # "https://es.wisuki.com/forecast/2842/playa-del-risco",
        # "https://es.wisuki.com/forecast/5987/orzola",
        # "https://es.wisuki.com/forecast/2834/jameos-del-agua",
        # "https://es.wisuki.com/forecast/2841/playa-de-la-garita",
        # "https://es.wisuki.com/forecast/7183/playa-jablillo",
        # "https://es.wisuki.com/forecast/2844/playa-honda",
        # "https://es.wisuki.com/forecast/2839/matagorda",
        # "https://es.wisuki.com/forecast/8496/playa-chica",
        # "https://es.wisuki.com/forecast/2843/playa-dorada",
    ]

    plot_forecast(urls)
    plot_tides()
