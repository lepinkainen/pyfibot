# -*- coding: utf-8 -*-
from __future__ import print_function, division
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

    r = bot.get_url(url % location)
    if 'cod' in r.json() and r.json()['cod'] == '200':
        if 'list' in r.json():
            data = r.json()['list'][0]
            location = data['name']

            if 'dt' in data:
                measured = datetime.utcfromtimestamp(data['dt'])
                if datetime.utcnow() - timedelta(minutes=threshold) > measured:
                    text = '%s (%s UTC): ' % (location, measured.strftime('%Y-%m-%d %H:%M'))
                else:
                    text = '%s: ' % location
            else:
                text = '%s: ' % location

            main = data['main']
            if 'temp' in main:
                temperature = main['temp'] - 273.15  # temperature converted from kelvins to celcius and rounded
                text += 'Temperature: %.1fc' % temperature
            else:
                temperature = None
            if 'wind' in data and 'speed' in data['wind']:
                wind = data['wind']['speed']  # Wind speed in mps (m/s)
            else:
                wind = None
            if temperature and wind:
                feels_like = 13.12 + 0.6215 * temperature - 11.37 * (wind * 3.6) ** 0.16 + 0.3965 * temperature * (wind * 3.6) ** 0.16
                text += ', Feels like: %.1fc' % feels_like
            if wind:
                text += ', Wind: %.1f m/s' % wind
            if 'humidity' in main:
                humidity = main['humidity']  # Humidity in %
                text += ', Humidity: %d%%' % humidity
            if 'pressure' in main:
                pressure = main['pressure']  # Atmospheric pressure in hPa
                text += ', Pressure: %d hPa' % pressure
            if 'clouds' in data and 'all' in data['clouds']:
                cloudiness = data['clouds']['all']  # Cloudiness in %
                text += ', Cloudiness: %d%%' % cloudiness

            return bot.say(channel, text)
    else:
        return bot.say(channel, 'Error: Location not found.')
