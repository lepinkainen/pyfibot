# -*- coding: utf-8 -*-
from __future__ import print_function, division, unicode_literals
import logging
from datetime import datetime, timedelta


log = logging.getLogger('openweather')
default_location = 'Helsinki'
threshold = 120


def init(bot):
    global default_location
    global threshold
    config = bot.config.get('module_openweather', {})
    default_location = config.get('default_location', 'Helsinki')
    threshold = int(config.get('threshold', 120))  # threshold to show measuring time in minutes
    log.info('Using %s as default location' % default_location)


def command_weather(bot, user, channel, args):
    global default_location
    global threshold
    if args:
        location = args.decode('utf-8')
    else:
        location = default_location

    url = 'http://openweathermap.org/data/2.5/weather?q=%s&units=metric'
    r = bot.get_url(url % location)

    if 'cod' not in r.json() or int(r.json()['cod']) != 200:
        return bot.say(channel, 'Error: API error.')
    data = r.json()

    if 'name' not in data:
        return bot.say(channel, 'Error: Location not found.')
    if 'main' not in data:
        return bot.say(channel, 'Error: Unknown error.')

    location = data['name']
    main = data['main']

    old_data = False
    if 'dt' in data:
        measured = datetime.utcfromtimestamp(data['dt'])
        if datetime.utcnow() - timedelta(minutes=threshold) > measured:
            old_data = True
    if old_data:
        text = '%s (%s UTC): ' % (location, measured.strftime('%Y-%m-%d %H:%M'))
    else:
        text = '%s: ' % location

    temperature = None
    if 'temp' in main:
        temperature = main['temp']  # temperature converted from kelvin to celcius
        text += u'Temperature: %.1f°C' % temperature
    if temperature is None:
        return bot.say(channel, 'Error: Temperature not found.')

    wind = None
    if 'wind' in data and 'speed' in data['wind']:
        wind = data['wind']['speed']  # Wind speed in mps (m/s)

    if temperature is not None and wind is not None:
        feels_like = 13.12 + 0.6215 * temperature - 11.37 * (wind * 3.6) ** 0.16 + 0.3965 * temperature * (wind * 3.6) ** 0.16
        text += ', feels like: %.1f°C' % feels_like

    if wind is not None:
        text += ', wind: %.1f m/s' % wind
    if 'humidity' in main:
        humidity = main['humidity']  # Humidity in %
        text += ', humidity: %d%%' % humidity
    if 'pressure' in main:
        pressure = main['pressure']  # Atmospheric pressure in hPa
        text += ', pressure: %d hPa' % pressure
    if 'clouds' in data and 'all' in data['clouds']:
        cloudiness = data['clouds']['all']  # Cloudiness in %
        text += ', cloudiness: %d%%' % cloudiness

    return bot.say(channel, text)
