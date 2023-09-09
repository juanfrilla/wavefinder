from pydantic import BaseModel
from typing import List, Dict
from utils import (
    degrees_to_direction,
    get_datename,
    timestamp_to_datetimestr,
    classify_wind_speed,
)
import json


class Wind(BaseModel):
    directionType: str = ""
    direction: float = -999.0
    speed: float = -999.0

    @property
    def wind_direction(self) -> int:
        return degrees_to_direction(self.direction)

    @property
    def wind_description(self) -> str:
        return classify_wind_speed(self.speed)


class Swell(BaseModel):
    direction: float = -999.0

    @property
    def swell_direction(self) -> int:
        return degrees_to_direction(self.direction)

    period: int


class Surf(BaseModel):
    humanRelation: str
    min: float
    max: float

    @property
    def swell_size(self) -> str:
        min_val = self.min
        max_val = self.max
        return max_val


class Wave(BaseModel):
    timestamp: int
    utcOffset: int

    @property
    def date(self) -> str:
        return timestamp_to_datetimestr(self.timestamp, self.utcOffset)[0]

    @property
    def date_name(self) -> str:
        return get_datename(self.date)

    @property
    def time(self) -> str:
        return timestamp_to_datetimestr(self.timestamp, self.utcOffset)[1]

    surf: Surf
    swells: List[Swell]

    @property
    def swell_direction(self) -> str:
        if self.swells:
            return self.swells[0].swell_direction
        return None

    @property
    def period(self) -> str:
        if self.swells:
            return self.swells[0].period
        return None

    @property
    def swell_size(self) -> str:
        return self.surf.swell_size


class Condition(BaseModel):
    pass


class Rating(BaseModel):
    rating: Dict

    @property
    def rating_key(self):
        return self.rating.get("key", "")


class Tide(BaseModel):
    type: str
    height: float


class TideLocation(BaseModel):
    name: str


class TideData(BaseModel):
    tideLocation: TideLocation
    data: List[Tide]

    def from_tide_dict(self):
        tide_location_data = self.tideLocation
        tide_location = TideLocation(**tide_location_data)
        tides = [Tide(**tide) for tide in self.data]
        return TideData(tideLocation=tide_location, data=tides)

    @property
    def tide_status(self) -> str:
        tide_statuses = []
        for element in self.data:
            tide_statuses.append(element.type)
        return tide_statuses

    @property
    def tide_height(self) -> int:
        return self.data.height

    @property
    def beach(self) -> str:
        return self.tideLocation.name


class Item(BaseModel):
    date_name: str
    date: str
    time: str
    spot_name: str
    wind_status: str
    tide_state: str
    tide_height: float
    # tides_hour: str
    # flatness: str
    # primary_wave: str
    wave_period: int
    # swell_rate: str
    wave_height: float
    wind_direction: str
    wave_direction: str
    wind_description: str
    page_rating: str
    approval: str

    @staticmethod
    def calculate_approval(wind_direction, period, wave_height) -> str:
        if (
            # "offshore" in wind_direction.lower()
            period >= 6
            and wave_height >= 1
        ):
            return "Favorable"
        return "No Favorable"

    # island: str
    # webcam: str
