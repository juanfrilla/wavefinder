from scrapers.windfinder import WindFinder
from scrapers.windguru import Windguru


# def test_playa_blanca():
#     windfinder = WindFinder()
#     soup = windfinder.sample_soup("./samples/playa_blanca.html")
#     wave_directions = windfinder.parse_wave_directions(soup)
#     wind_directions = windfinder.parse_wind_directions(soup)
#     total_records = len(wave_directions)

#     assert len(windfinder.parse_dates_str(soup, total_records)) == 80
#     assert len(windfinder.parse_spot_names(soup, total_records)) == 80
#     assert len(windfinder.parse_hour_intervals(soup)) == 80
#     assert len(windfinder.parse_wave_periods(soup)) == 80
#     assert len(windfinder.parse_wave_heights(soup)) == 80
#     assert len(windfinder.parse_windstatus(wave_directions, wind_directions)) == 80


# def test_costa_teguise():
#     windfinder = WindFinder()
#     soup = windfinder.sample_soup("./samples/costa_teguise.html")
#     wave_directions = windfinder.parse_wave_directions(soup)
#     wind_directions = windfinder.parse_wind_directions(soup)
#     total_records = len(wave_directions)

#     assert len(windfinder.parse_dates_str(soup, total_records)) == 80
#     assert len(windfinder.parse_spot_names(soup, total_records)) == 80
#     assert len(windfinder.parse_hour_intervals(soup)) == 80
#     assert len(windfinder.parse_wave_periods(soup)) == 80
#     assert len(windfinder.parse_wave_heights(soup)) == 80
#     assert len(windfinder.parse_windstatus(wave_directions, wind_directions)) == 80
#     assert len(windfinder.parse_wave_directions(soup)) == 80
#     assert len(windfinder.parse_wind_directions(soup)) == 80
    
def test_wind_speed():
    windfinder = WindFinder()
    soup = windfinder.sample_soup("./samples/costa_teguise.html")
    wind_speeds = windfinder.parse_wind_speeds(soup)
    
    assert len(wind_speeds) == 1

def test_common():
    windfinder = WindFinder()
    ct_soup = windfinder.sample_soup("./samples/costa_teguise.html")
    pb_soup = windfinder.sample_soup("./samples/playa_blanca.html")
    
    ct_wave_directions = windfinder.parse_wave_directions(ct_soup)
    pb_wave_directions = windfinder.parse_wave_directions(pb_soup)
    ct_total_records = len(ct_wave_directions)
    pb_total_records = len(pb_wave_directions)
    
    assert ct_total_records == pb_total_records
    

# def test_windfinder_200_ok():
#     windfinder = WindFinder()
#     response = windfinder.beach_request("https://es.windfinder.com/forecast/lanzarote_playa_de_las_cucharas_costa_te")
#     assert response.status_code == 200
#     response = windfinder.beach_request("https://es.windfinder.com/forecast/famara")
#     assert response.status_code == 200
#     response = windfinder.beach_request("https://es.windfinder.com/forecast/la_palma1")
#     assert response.status_code == 200
#     response = windfinder.beach_request("https://es.windfinder.com/forecast/jameos_del_agua")
#     assert response.status_code == 200
    
# def test_windguru_date_backslash():
#     windguru = Windguru()
#     assert windguru.datestr_to_backslashformat("Fr25") == "25/08/2023"
#     assert windguru.datestr_to_backslashformat("Sa26") == "26/08/2023"
#     assert windguru.datestr_to_backslashformat("Sa9") == "09/09/2023"