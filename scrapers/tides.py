from bs4 import BeautifulSoup
import os, datetime, polars as pl
from typing import Dict
from requests import Session
from utils import get_day_name, datestr_to_datetime
from datetime import datetime, timedelta


class TidesScraper(object):
    def __init__(self):
        pass

    def construct_year_tides(self, start_tide_event: dict) -> list:
        """
        Generate a year-long list of tides starting from a given tide event.
    
        Args:
            start_tide_event (dict): A dictionary with keys "datetime" (datetime object)
                                     and "tide" (either "pleamar" or "bajamar").
    
        Returns:
            list: A list of dictionaries, each with keys "datetime" and "tide".
        """
        tide_interval = timedelta(hours=6, minutes=12, seconds=30)
        tides = [start_tide_event.copy()]
        
        current_time = start_tide_event["datetime"]
        current_tide = start_tide_event["tide"]
        end_time = current_time + timedelta(days=365)
    
        while current_time <= end_time:
            current_time += tide_interval
            current_tide = "pleamar" if current_tide == "bajamar" else "bajamar"
            tides.append({"datetime": current_time, "tide": current_tide})
    
        return tides
        
    def tasks(self):
        start_event = {
            "datetime": datetime(2025, 4, 1, 16, 32),
            "tide": "pleamar"
        }
        
        tides = self.construct_year_tides(start_event)
        return tides
