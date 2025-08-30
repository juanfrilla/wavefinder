import polars as pl
from utils import generate_spot_name, calculate_energy


def test_separate_spots():

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
    ) == "El Espino"
    assert (
        generate_spot_name(
            wind_direction_predominant="NW",
            wind_direction="NW",
            wave_direction_predominant="NW",
            wave_direction="NW",
            wind_speed=12,
            wave_period=10,
            wave_energy=calculate_energy(wave_height=2.5, wave_period=10),
            tide_percentage=20,
        )
    ) == "El Cartel"

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
    ) == "Papagayo - Montaña Amarilla"

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

    assert (
        generate_spot_name(
            wind_direction_predominant="NE",
            wind_direction="NE",
            wave_direction_predominant="N",
            wave_direction="N",
            wind_speed=20,
            wave_period=13,
            wave_energy=calculate_energy(wave_height=2.2, wave_period=13),
            tide_percentage=10,
        )
        == "Barcarola"
    )

    assert (
        generate_spot_name(
            wind_direction_predominant="NE",
            wind_direction="NE",
            wave_direction_predominant="N",
            wave_direction="N",
            wind_speed=20,
            wave_period=13,
            wave_energy=calculate_energy(wave_height=2.2, wave_period=13),
            tide_percentage=60,
        )
        == "Bastián"
    )
    assert (
        generate_spot_name(
            wind_direction_predominant="NW",
            wind_direction="WNW",
            wave_direction_predominant="WNW",
            wave_direction="NW",
            wind_speed=20,
            wave_period=13,
            wave_energy=calculate_energy(wave_height=4, wave_period=15),
            tide_percentage=60,
        )
        == "Tiburón-Espino"
    )
    assert (
        generate_spot_name(
            wind_direction_predominant="NE",
            wind_direction="NNE",
            wave_direction_predominant="WNW",
            wave_direction="NW",
            wind_speed=20,
            wave_period=13,
            wave_energy=calculate_energy(wave_height=4, wave_period=15),
            tide_percentage=60,
        )
        == "Posible Tiburón"
    )
    assert (
        generate_spot_name(
            wind_direction_predominant="N",
            wind_direction="N",
            wave_direction_predominant="WNW",
            wave_direction="NW",
            wind_speed=20,
            wave_period=13,
            wave_energy=calculate_energy(wave_height=4, wave_period=15),
            tide_percentage=60,
        )
        == "Tiburón-Espino"
    )
    assert (
        generate_spot_name(
            wind_direction_predominant="W",
            wind_direction="WNW",
            wave_direction_predominant="WNW",
            wave_direction="NW",
            wind_speed=6,
            wave_period=13,
            wave_energy=calculate_energy(wave_height=2.2, wave_period=13),
            tide_percentage=60,
        )
        == "San Juan - Cagao - El Muelle"
    )

    assert (
        generate_spot_name(
            wind_direction_predominant="SE",
            wind_direction="ESE",
            wave_direction_predominant="NW",
            wave_direction="WNW",
            wind_speed=12,
            wave_period=13,
            wave_energy=calculate_energy(wave_height=2.2, wave_period=13),
            tide_percentage=60,
        )
        == "Papelillo"
    )
    assert (
        generate_spot_name(
            wind_direction_predominant="S",
            wind_direction="SSE",
            wave_direction_predominant="NW",
            wave_direction="WNW",
            wind_speed=7,
            wave_period=13,
            wave_energy=calculate_energy(wave_height=2.2, wave_period=13),
            tide_percentage=60,
        )
        == "Papelillo - Bajo el Risco"
    )


test_separate_spots()
