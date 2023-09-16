from front import plot_forecast, plot_tides

if __name__ == "__main__":
    urls = [
        "https://www.worldbeachguide.com/spain/surf/costa-teguise.htm",
        #"https://www.worldbeachguide.com/spain/surf/punta-de-mujeres.htm"
    ]

    plot_forecast(urls)
    plot_tides()
