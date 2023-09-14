from bs4 import BeautifulSoup
import requests
import pandas as pd
from utils import (
    rename_key,
    angle_to_direction,
    get_wind_status,
    render_html,
    open_browser
)
from datetime import datetime, timedelta
import re


class WindyApp(object):
    def __init__(self):
        pass
    
    def beach_request(self, browser, url):
        r_text = render_html(
            browser=browser, url=url, tag_to_wait="tr.windywidgetdays", timeout=10
        )
        return BeautifulSoup(r_text, "html.parser")
    
    def scrape(self, browser, url):
        soup = self.beach_request(browser, url)
        date = soup.select("tr.windywidgetdays > td")
        time = soup.select("tr.windywidgethours > td")
        wind_direction = soup.select("tr.windywidgetwindDirection.id-wind-direction > td")
        wind_speed = soup.select("tr.windywidgetwindSpeed.id-wind-speed > td")
        waves_direction = soup.select("tr.windywidgetwaves.id-waves-direction > td")
        waves_heigth = soup.select("tr.windywidgetwavesheight.id-waves-height > td")
        waves_period = soup.select("windywidgetwavesperiod.id-waves-period > td")
        print()
        #return self.process_soup(soup)


