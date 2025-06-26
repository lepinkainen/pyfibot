# -*- encoding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from math import isnan

global default_place
default_place = "Helsinki"

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


def init(bot):
    global default_place
    config = bot.config.get("module_fmi", {})
    default_place = config.get("default_place", default_place)


def command_saa(bot, user, channel, args):
    """Command to fetch data from FMI"""
    if args:
        place = args
    else:
        place = default_place

    starttime = (datetime.utcnow() - timedelta(minutes=10)).strftime(TIME_FORMAT) + "Z"
    params = {
        "request": "getFeature",
        "storedquery_id": "fmi::observations::weather::timevaluepair",
        "parameters": ",".join(PARAMETERS),
        "crs": "EPSG::3067",
        "place": place,
        "maxlocations": 1,
        "starttime": starttime,
    }

    r = bot.get_url("http://opendata.fmi.fi/wfs", params=params)
    bs = BeautifulSoup(r.text)

    # Get FMI name, gives the observation place more accurately
    try:
        place = bs.find("gml:name").text
    except AttributeError:
        return bot.say(channel, "Paikkaa ei löytynyt.")

    # Loop through measurement time series -objects and gather values
    values = {}
    for mts in bs.find_all("wml2:measurementtimeseries"):
        # Get the identifier from mts-tag
        target = mts["gml:id"].split("-")[-1]
        # Get last value from measurements (always sorted by time)
        value = float(mts.find_all("wml2:value")[-1].text)
        # NaN is returned, if observation doesn't exist
        if not isnan(value):
            values[target] = value

    # Build text from values found
    text = []
    if "t2m" in values:
        text.append("lämpötila: %.1f°C" % values["t2m"])
    if "t2m" in values and "ws_10min" in values:
        # Calculate "feels like" if both temperature and wind speed were found
        feels_like = (
            13.12
            + 0.6215 * values["t2m"]
            - 13.956 * (values["ws_10min"] ** 0.16)
            + 0.4867 * values["t2m"] * (values["ws_10min"] ** 0.16)
        )
        text.append("tuntuu kuin: %.1f°C" % feels_like)
    if "ws_10min" in values:
        text.append("tuulen nopeus: %i m/s" % round(values["ws_10min"]))
    if "rh" in values:
        text.append("ilman kosteus: %i%%" % round(values["rh"]))
    if "n_man" in values:
        text.append("pilvisyys: %i/8" % int(values["n_man"]))
    if "wawa" in values and int(values["wawa"]) in WAWA:
        text.append(WAWA[int(values["wawa"])])

    # Return place and values to the channel
    return bot.say(channel, "%s: %s" % (place, ", ".join(text)))


def command_keli(bot, user, channel, args):
    """Alias for command "saa" """
    return command_saa(bot, user, channel, args)
