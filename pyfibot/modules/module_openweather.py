# -*- coding: utf-8 -*-
from __future__ import print_function, division, unicode_literals
import logging
from datetime import date, datetime, timedelta


log = logging.getLogger("openweather")
default_location = "Helsinki"
threshold = 120

appid = None


def init(bot):
    global appid
    global default_location
    global threshold

    config = bot.config.get("module_openweather", {})
    default_location = config.get("default_location", "Helsinki")
    log.info("Using %s as default location" % default_location)

    appid = config.get("appid")
    if appid:
        log.info("Using OpenWeatherMap appid %s" % appid)
    else:
        log.warning("Appid not found!")

    threshold = int(
        config.get("threshold", 120)
    )  # threshold to show measuring time in minutes


def command_weather(bot, user, channel, args):
    """Weather from openweathermap"""
    if not appid:
        log.warn("No OpenWeatherMap appid set in configuration")
        return False

    global default_location
    global threshold
    if args:
        location = args
    else:
        location = default_location

    url = "http://api.openweathermap.org/data/2.5/weather?q=%s&units=metric&appid=%s"
    r = bot.get_url(url % (location, appid))

    try:
        data = r.json()
    except:
        log.debug("Couldn't parse JSON.")
        return bot.say(channel, "Error: API error, unable to parse JSON response.")

    if "cod" not in data or int(data["cod"]) != 200:
        log.debug("status != 200")
        return bot.say(channel, "Error: API error.")

    if "name" not in data:
        return bot.say(channel, "Error: Location not found.")
    if "main" not in data:
        return bot.say(channel, "Error: Unknown error.")

    location = "%s, %s" % (data["name"], data["sys"]["country"])
    main = data["main"]

    old_data = False
    if "dt" in data:
        measured = datetime.utcfromtimestamp(data["dt"])
        if datetime.utcnow() - timedelta(minutes=threshold) > measured:
            old_data = True
    if old_data:
        text = "%s (%s UTC): " % (location, measured.strftime("%Y-%m-%d %H:%M"))
    else:
        text = "%s: " % location

    if "temp" not in main:
        return bot.say(channel, "Error: Data not found.")

    temperature = main["temp"]  # temperature converted from kelvin to celcius
    text += "Temperature: %.1f°C" % temperature

    if "wind" in data and "speed" in data["wind"]:
        wind = data["wind"]["speed"]  # Wind speed in mps (m/s)

        feels_like = (
            13.12
            + 0.6215 * temperature
            - 13.956 * (wind**0.16)
            + 0.4867 * temperature * (wind**0.16)
        )
        text += ", feels like: %.1f°C" % feels_like
        text += ", wind: %.1f m/s" % wind

    if "humidity" in main:
        humidity = main["humidity"]  # Humidity in %
        text += ", humidity: %d%%" % humidity
    if "pressure" in main:
        pressure = main["pressure"]  # Atmospheric pressure in hPa
        text += ", pressure: %d hPa" % pressure
    if "clouds" in data and "all" in data["clouds"]:
        cloudiness = data["clouds"]["all"]  # Cloudiness in %
        text += ", cloudiness: %d%%" % cloudiness

    return bot.say(channel, text)


def command_forecast(bot, user, channel, args):
    global default_location
    if not appid:
        log.warn("No OpenWeatherMap appid set in configuration")
        return False

    if args:
        location = args
    else:
        location = default_location

    url = "http://api.openweathermap.org/data/2.5/forecast/daily?q=%s&cnt=5&mode=json&units=metric&appid=%s"
    r = bot.get_url(url % (location, appid))

    try:
        data = r.json()
    except:
        log.debug("Couldn't parse JSON.")
        return bot.say(channel, "Error: API error, unable to parse JSON response.")

    if "cod" not in data or int(data["cod"]) != 200:
        log.debug("status != 200")
        return bot.say(channel, "Error: API error.")

    if "city" not in data or "name" not in data["city"]:
        return bot.say(channel, "Error: Location not found.")

    if not data["list"]:
        return bot.say(channel, "Error: No forecast data.")

    text = "%s, %s: " % (data["city"]["name"], data["city"]["country"])

    cur_date = date.today()
    forecast_text = []
    for d in data["list"]:
        forecast_date = date.fromtimestamp(d["dt"])
        date_delta = (forecast_date - cur_date).days

        if date_delta < 1:
            continue

        if date_delta == 1:
            forecast_text.append(
                "tomorrow: %.1f - %.1f °C (%s)"
                % (d["temp"]["min"], d["temp"]["max"], d["weather"][0]["description"])
            )
        else:
            forecast_text.append(
                "in %d days: %.1f - %.1f °C (%s)"
                % (
                    date_delta,
                    d["temp"]["min"],
                    d["temp"]["max"],
                    d["weather"][0]["description"],
                )
            )

        if len(forecast_text) >= 3:
            break

    text += ", ".join(forecast_text)
    return bot.say(channel, text)
