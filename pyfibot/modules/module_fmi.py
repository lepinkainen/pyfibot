# -*- encoding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from datetime import datetime, timedelta, timezone
from math import isnan
from typing import Optional
import logging

import lxml.etree as etree
import requests_cache
from tenacity import retry, stop_after_attempt, wait_exponential
from pydantic import BaseModel, Field, field_validator

global default_place
default_place = "Helsinki"

log = logging.getLogger("fmi")

# Initialize cached session for API requests (15 minute cache)
cached_session = requests_cache.CachedSession(
    "fmi_cache", expire_after=900, backend="memory"  # 15 minutes
)


class WeatherData(BaseModel):
    """Pydantic model for weather data validation"""

    place: str = Field(..., description="Location name")
    temperature: Optional[float] = Field(None, description="Temperature in Celsius")
    feels_like: Optional[float] = Field(None, description="Feels like temperature")
    wind_speed: Optional[float] = Field(None, description="Wind speed in m/s")
    humidity: Optional[int] = Field(None, description="Relative humidity percentage")
    cloudiness: Optional[int] = Field(None, description="Cloudiness 0-8")
    weather_description: Optional[str] = Field(None, description="Weather description")

    @field_validator("humidity", "cloudiness", mode="before")
    @classmethod
    def validate_percentages(cls, v):
        if v is not None and (v < 0 or v > 100):
            return None
        return v


# Time format for the API
TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
# t2m = temperature
# ws_10min = wind speed (10 min avg)
# rh == relative humidity
# n_man == cloudiness
# wawa == weather description number
PARAMETERS = ["t2m", "ws_10min", "rh", "n_man", "wawa"]

# http://ilmatieteenlaitos.fi/avoin-data-saahavainnot
WAWA = {
    10: "utua",
    20: "sumua",
    21: "sadetta",
    22: "tihkusadetta",
    23: "vesisadetta",
    24: "lumisadetta",
    25: "jäätävää tihkua",
    30: "sumua",
    31: "sumua",
    32: "sumua",
    33: "sumua",
    34: "sumua",
    40: "sadetta",
    41: "heikkoa tai kohtalaista sadetta",
    42: "kovaa sadetta",
    50: "tihkusadetta",
    51: "heikkoa tihkusadetta",
    52: "kohtalaista tihkusadetta",
    53: "kovaa tihkusadetta",
    54: "jäätävää heikkoa tihkusadetta",
    55: "jäätävää kohtalaista tihkusadetta",
    56: "jäätävää kovaa tihkusadetta",
    60: "vesisadetta",
    61: "heikkoa vesisadetta",
    62: "kohtalaista vesisadetta",
    63: "kovaa vesisadetta",
    64: "jäätävää heikkoa vesisadetta",
    65: "jäätävää kohtalaista vesisadetta",
    66: "jäätävää kovaa vesisadetta",
    67: "räntää",
    68: "räntää",
    70: "lumisadetta",
    71: "heikkoa lumisadetta",
    72: "kohtalaista lumisadetta",
    73: "tiheää lumisadetta",
    74: "heikkoa jääjyväsadetta",
    75: "kohtalaista jääjyväsadetta",
    76: "kovaa jääjyväsadetta",
    77: "lumijyväsiä",
    78: "jääkiteitä",
    80: "sadekuuroja",
    81: "heikkoja sadekuuroja",
    82: "kohtalaisia sadekuuroja",
    84: "heikkoja lumikuuroja",
    85: "kohtalaisia lumikuuroja",
    86: "kovia lumikuuroja",
    87: "raekuuroja",
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def _fetch_weather_data(place: str) -> Optional[WeatherData]:
    """Fetch weather data from FMI API with retry logic and caching"""
    starttime = (datetime.now(timezone.utc) - timedelta(minutes=10)).strftime(
        TIME_FORMAT
    ) + "Z"
    params = {
        "request": "getFeature",
        "storedquery_id": "fmi::observations::weather::timevaluepair",
        "parameters": ",".join(PARAMETERS),
        "crs": "EPSG::3067",
        "place": place,
        "maxlocations": 1,
        "starttime": starttime,
    }

    try:
        response = cached_session.get(
            "http://opendata.fmi.fi/wfs", params=params, timeout=10
        )
        response.raise_for_status()

        # Parse XML with lxml for better performance
        root = etree.fromstring(response.content)

        # Define namespaces
        namespaces = {
            "gml": "http://www.opengis.net/gml/3.2",
            "wml2": "http://www.opengis.net/waterml/2.0",
        }

        # Get FMI name for more accurate location
        name_element = root.find(".//gml:name", namespaces)
        if name_element is None:
            log.warning(f"Location not found: {place}")
            return None

        location_name = name_element.text

        # Extract measurement values
        values = {}
        for mts in root.findall(".//wml2:MeasurementTimeseries", namespaces):
            gml_id = mts.get("{http://www.opengis.net/gml/3.2}id")
            if gml_id:
                target = gml_id.split("-")[-1]
                value_elements = mts.findall(".//wml2:value", namespaces)
                if value_elements:
                    try:
                        value = float(value_elements[-1].text)
                        if not isnan(value):
                            values[target] = value
                    except (ValueError, TypeError):
                        continue

        # Calculate feels like temperature if we have both temp and wind
        feels_like = None
        if "t2m" in values and "ws_10min" in values:
            feels_like = (
                13.12
                + 0.6215 * values["t2m"]
                - 13.956 * (values["ws_10min"] ** 0.16)
                + 0.4867 * values["t2m"] * (values["ws_10min"] ** 0.16)
            )

        # Get weather description
        weather_desc = None
        if "wawa" in values and int(values["wawa"]) in WAWA:
            weather_desc = WAWA[int(values["wawa"])]

        # Create and validate weather data
        weather_data = WeatherData(
            place=location_name,
            temperature=values.get("t2m"),
            feels_like=feels_like,
            wind_speed=values.get("ws_10min"),
            humidity=int(values["rh"]) if "rh" in values else None,
            cloudiness=int(values["n_man"]) if "n_man" in values else None,
            weather_description=weather_desc,
        )

        return weather_data

    except Exception as e:
        log.error(f"Error fetching weather data for {place}: {e}")
        raise


def init(bot):
    global default_place
    config = bot.config.get("module_fmi", {})
    default_place = config.get("default_place", default_place)


def command_saa(bot, user, channel, args):
    """Command to fetch data from FMI with enhanced error handling and caching"""
    place = args if args else default_place

    try:
        weather_data = _fetch_weather_data(place)
        if not weather_data:
            return bot.say(channel, "Paikkaa ei löytynyt.")

        # Build text from weather data
        text_parts = []

        if weather_data.temperature is not None:
            text_parts.append(f"lämpötila: {weather_data.temperature:.1f}°C")

        if weather_data.feels_like is not None:
            text_parts.append(f"tuntuu kuin: {weather_data.feels_like:.1f}°C")

        if weather_data.wind_speed is not None:
            text_parts.append(f"tuulen nopeus: {round(weather_data.wind_speed)} m/s")

        if weather_data.humidity is not None:
            text_parts.append(f"ilman kosteus: {weather_data.humidity}%%")

        if weather_data.cloudiness is not None:
            text_parts.append(f"pilvisyys: {weather_data.cloudiness}/8")

        if weather_data.weather_description:
            text_parts.append(weather_data.weather_description)

        if not text_parts:
            return bot.say(channel, f"{weather_data.place}: ei säätietoja saatavilla")

        response = f"{weather_data.place}: {', '.join(text_parts)}"
        return bot.say(channel, response)

    except Exception as e:
        log.error(f"Weather command failed for {place}: {e}")
        return bot.say(channel, f"Säätietojen haku epäonnistui: {place}")


def command_keli(bot, user, channel, args):
    """Alias for command "saa" """
    return command_saa(bot, user, channel, args)
