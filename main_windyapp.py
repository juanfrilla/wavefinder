from front import plot_forecast, plot_tides

if __name__ == "__main__":
    urls = [
        "https://windy.app/forecast2/spot/4016175/El%20Espino",
        "https://windy.app/forecast2/spot/5320955/Castillo+rubicon",
        "https://windy.app/forecast2/spot/302072/Beach+Honda+Spain+Playa+Honda",
        "https://windy.app/forecast2/spot/647997/Faro+de+Pechiguera",
        "https://windy.app/forecast2/spot/5074651/puente+las+bolas",
        "https://windy.app/forecast2/spot/5334017/chucara",
        "https://windy.app/forecast2/spot/302056/Spain%20-%20Los%20Pocillos",
        "https://windy.app/forecast2/spot/4016189/Playa%20de%20Orzola",
        "https://windy.app/forecast2/spot/4016187/Playa%20de%20las%20Conchas",
        "https://windy.app/forecast2/spot/2648709/Puerto+Caleta+del+Sebo",
        "https://windy.app/forecast2/spot/4974331/Playa+del+labar",
        "https://windy.app/forecast2/spot/273242/Caleta+de+Famara+Spain",
        "https://windy.app/forecast2/spot/4698931/la+santa",
        "https://windy.app/forecast2/spot/4016191/Ghost+Town",
    ]

    plot_forecast(urls)
    plot_tides()
