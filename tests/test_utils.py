import polars as pl
from utils import separate_spots


# Define a test DataFrame
def test_separate_spots():
    test_data = {
        "wind_direction_predominant": ["W", "E", "N", "NE", "S"],
        "wind_direction": ["W", "E", "NE", "S", "W"],
        "wave_direction": ["N", "E", "W", "E", "N"],
        "wave_direction_predominant": ["N", "E", "W", "S", "E"],
        "wind_speed": [5, 12, 22, 19, 10],
        "tide_percentage": [30, 60, 50, 40, 50],
        "wave_height": [1.5, 1.9, 2.1, 1.7, 2.2],
        "wave_period": [8.0, 9.5, 10.5, 8.0, 11.0],
    }
    df = pl.DataFrame(test_data)

    result_df = separate_spots(df)

    spot_names = result_df["spot_name"].to_list()
    expected_results = [
        "Papagayo",
        "Papelillo",
        "No Clasificado",
        "No Clasificado",
        "No Clasificado",
    ]
    assert (
        spot_names == expected_results
    ), f"Expected {expected_results}, but got {spot_names}"

    print("All test cases passed!")



test_separate_spots()
