# -*- coding: utf-8 -*-
import requests
import logging


log = logging.getLogger('openweather')
url = 'http://openweathermap.org/data/2.1/find/name?q=%s'


def init(bot):
    global default_location
    config = bot.config.get("module_openweather", {})
    default_location = config.get("default_location", "Helsinki")
    log.info('Using %s as default location' % default_location)


def command_weather(bot, user, channel, args):
    global default_location
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

            text = '%s: Temperature: %.1fc, Humidity: %d%%, Pressure: %d hPa, Wind: %.1f m/s, Cloudiness: %d%%' % (location, temperature, humidity, pressure, wind, cloudiness)
            text = text.encode('utf-8')
            return bot.say(channel, text)
    else:
        return bot.say(channel, 'Error: Location not found.')
