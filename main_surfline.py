import warnings

warnings.filterwarnings("ignore")
from front import plot_forecast, plot_tides


def main():
    spots_ids = [
        "640b8a024519052897dbddab",  # CASTILLO
        "584204204e65fad6a77096ab",  # CALETA_CABALLO
        "584204204e65fad6a77096ac",  # FAMARA
        "640b8a204878eb7c4b199ac5",  # SAN JUAN
        "640b8a0e606c451bb9efd06e",  # GHOST TOWN
        "584204204e65fad6a77096aa",  # JANUBIO
        "640b89dee920301df8dcfb78",  # ORZOLA, CANTERIA
        "640b8a08de81d507f709844a",  # IZQUIERDA LA SANTA
        "640b8a14e920300eafdd0979",  # MATAGORDA
        "640b8a1be92030121ddd0ad7",  # LAS CUCHARAS
        "640b89f6b6d7690d55905b35",  # ARRIETA
        "640b89fc8284fedebeacd97e",  # EL ESPINO
        "584204204e65fad6a77096a9",  # JAMEOS
        "640b89f0606c45fd2cefc818",  # LAS CONCHAS
    ]

    plot_forecast(spots_ids)
    plot_tides()


if __name__ == "__main__":
    main()
