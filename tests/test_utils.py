import polars as pl
from utils import generate_spot_name, calculate_energy


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
            "E",
            "NW",
            "SE",
            "NE",
        ],
        "wind_direction": [
            "W",
            "S",
            "NW",
            "E",
            "N",
            "S",
            "E",
            "W",
            "NW",
            "E",
            "NW",
            "SE",
            "NNE",
        ],
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
            "NW",
            "WNW",
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
            "NW",
            "NW",
        ],
        "wind_speed": [5, 11, 12, 10, 7, 7, 11, 17, 1, 1, 1, 20, 3],
        "wave_height": [1.5, 2.0, 2.5, 2.5, 2.5, 2.5, 2.0, 3, 1.5, 1.7, 2.2, 2.2, 2.1],
        "wave_period": [
            8.0,
            9.0,
            10.0,
            12.0,
            13.0,
            10.0,
            10.0,
            12.0,
            9.0,
            10.0,
            13.0,
            12.0,
            11.0,
        ],
        "tide_percentage": [60, 60, 90, 10, 10, 80, 0, 60, 60, 10, 50, 10, 28],
    }

    assert (
        generate_spot_name(
            wind_direction_predominant="W",
            wind_direction="W",
            wave_direction_predominant="N",
            wave_direction="N",
            wind_speed=5,
            wave_period=8,
            wave_energy=calculate_energy(wave_height=1.5, wave_period=8),
            tide_percentage=60,
        )
        == "Caleta Caballo"
    )
    assert (
        generate_spot_name(
            wind_direction_predominant="S",
            wind_direction="S",
            wave_direction_predominant="N",
            wave_direction="N",
            wind_speed=11,
            wave_period=9,
            wave_energy=calculate_energy(wave_height=2.0, wave_period=9),
            tide_percentage=60,
        )
    ) == "Famara"

    assert (
        generate_spot_name(
            wind_direction_predominant="NW",
            wind_direction="NW",
            wave_direction_predominant="NW",
            wave_direction="NW",
            wind_speed=12,
            wave_period=10,
            wave_energy=calculate_energy(wave_height=2.5, wave_period=10),
            tide_percentage=90,
        )
    ) == "Punta Mujeres"

    assert (
        generate_spot_name(
            wind_direction_predominant="E",
            wind_direction="E",
            wave_direction_predominant="WNW",
            wave_direction="NW",
            wind_speed=10,
            wave_period=12,
            wave_energy=calculate_energy(wave_height=2.5, wave_period=12),
            tide_percentage=10,
        )
    ) == "Papagayo-Tiburón (Fuerza oeste - vacía)"

    assert (
        generate_spot_name(
            wind_direction_predominant="S",
            wind_direction="S",
            wave_direction_predominant="N",
            wave_direction="N",
            wind_speed=7,
            wave_period=10,
            wave_energy=calculate_energy(wave_height=2.5, wave_period=10),
            tide_percentage=80,
        )
    ) == "San Juan - Cagao - El Muelle"
    assert (
        generate_spot_name(
            wind_direction_predominant="E",
            wind_direction="E",
            wave_direction_predominant="NW",
            wave_direction="NW",
            wind_speed=17,
            wave_period=12,
            wave_energy=calculate_energy(wave_height=1, wave_period=12),
            tide_percentage=10,
        )
        == "Papelillo"
    )

    assert generate_spot_name(
        wind_direction_predominant="NE",
        wind_direction="NE",
        wave_direction_predominant="N",
        wave_direction="N",
        wind_speed=20,
        wave_period=13,
        wave_energy=calculate_energy(wave_height=2.2, wave_period=13),
        tide_percentage=10,
        ) == "Barcarola"

    assert generate_spot_name(
        wind_direction_predominant="NE",
        wind_direction="NE",
        wave_direction_predominant="N",
        wave_direction="N",
        wind_speed=20,
        wave_period=13,
        wave_energy=calculate_energy(wave_height=2.2, wave_period=13),
        tide_percentage=60,
        ) == "Bastián"


test_separate_spots()
