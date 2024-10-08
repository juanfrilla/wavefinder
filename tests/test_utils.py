import polars as pl
from utils import generate_spot_names, generate_energy


def test_separate_spots():
    test_data = {
        "wind_direction_predominant": [
            "W",
            "S",
            "NW",
            "E",
            "N",
            "S",
            "E",
            "SW",
            "NW",
            "N",
            "NW",
        ],
        "wind_direction": ["W", "S", "NW", "E", "N", "S", "E", "W", "NW", "NE", "NW"],
        "wave_direction": [
            "N",
            "N",
            "N",
            "WNW",
            "WNW",
            "N",
            "N",
            "NW",
            "NW",
            "N",
            "NW",
        ],
        "wave_direction_predominant": [
            "N",
            "N",
            "N",
            "NW",
            "NW",
            "N",
            "N",
            "NW",
            "NW",
            "N",
            "NW",
        ],
        "wind_speed": [5, 11, 12, 10, 7, 7, 11, 17, 1, 1, 1],
        "wave_height": [1.5, 2.0, 2.5, 2.0, 2.0, 2.5, 2.0, 3, 1.5, 1.7, 2.2],
        "wave_period": [8.0, 9.0, 10.0, 10.0, 10.0, 10.0, 10.0, 12.0, 10.0, 10.0, 13.0],
        "tide_percentage": [60, 60, 90, 10, 10, 80, 0, 60, 60, 10, 50],
    }
    test_data["energy"] = generate_energy(
        test_data["wave_height"], test_data["wave_period"]
    )

    spot_names = generate_spot_names(test_data)

    assert spot_names[0] == "Caleta Caballo"
    assert spot_names[1] == "Famara"
    assert spot_names[2] == "Punta Mujeres"
    assert spot_names[3] == "Papagayo-Tiburón (Fuerza oeste - vacía)"
    assert spot_names[4] == "Papagayo-Tiburón (Fuerza oeste - vacía)"
    assert spot_names[5] == "Famara"
    assert spot_names[6] == "Papelillo"
    assert spot_names[7] == "Caleta Caballo"
    assert spot_names[8] == "Caleta Caballo"
    assert spot_names[9] == "Papelillo"
    assert spot_names[10] == "Punta Mujeres"

    print("All test cases passed!")

    # TODO hacer para empate


test_separate_spots()
