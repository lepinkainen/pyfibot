# -*- coding: utf-8 -*-
import requests
import logging
from datetime import datetime, timedelta


log = logging.getLogger('openweather')
url = 'http://openweathermap.org/data/2.1/find/name?q=%s'


def init(bot):
    global default_location
    global threshold
    config = bot.config.get("module_openweather", {})
    default_location = config.get("default_location", "Helsinki")
    threshold = int(config.get("threshold", 120))  # threshold to show measuring time in minutes
    log.info('Using %s as default location' % default_location)


def command_weather(bot, user, channel, args):
    global default_location
    global threshold
    if args:
        location = args
    else:
        location = default_location
    r = requests.get(url % location)
    if 'cod' in r.json and r.json['cod'] == '200':
        if 'list' in r.json:
            data = r.json['list'][0]
            location = data['name']
            temperature = data['main']['temp'] - 273.15  # temperature converted from kelvins to celcius and rounded
            humidity = data['main']['humidity']  # Humidity in %
            pressure = data['main']['pressure']  # Atmospheric pressure in hPa
            wind = data['wind']['speed']  # Wind speed in mps (m/s)
            cloudiness = data['clouds']['all']  # Cloudiness in %
            measured = datetime.utcfromtimestamp(data['dt'])
            if datetime.utcnow() - timedelta(minutes=threshold) > measured:  # Shows measurement time if older than threshold
                text = '%s (%s UTC): Temperature: %.1fc, Humidity: %d%%, Pressure: %d hPa, Wind: %.1f m/s, Cloudiness: %d%%' % (location, measured.strftime('%Y-%m-%d %H:%M'), temperature, humidity, pressure, wind, cloudiness)
            else:
                text = '%s: Temperature: %.1fc, Humidity: %d%%, Pressure: %d hPa, Wind: %.1f m/s, Cloudiness: %d%%' % (location, temperature, humidity, pressure, wind, cloudiness)
            text = text.encode('utf-8')
            return bot.say(channel, text)
    else:
        return bot.say(channel, 'Error: Location not found.')
