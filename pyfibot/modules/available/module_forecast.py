# -*- coding: utf-8 -*-

"""
$Id$
$HeadURL$
"""

from __future__ import unicode_literals, print_function, division
import logging

log = logging.getLogger("forecast")

has_pywapi = False
try:
    import pywapi
    has_pywapi = True
except:
    log.error('Error loading library pywapi. Library not found.')


def fahrenheit_to_celcius(f):
    return (int(f) - 32) / 1.8


def command_forecast(bot, user, channel, args):
    """This module tells weather forecast for location"""
    if not has_pywapi:
        return

    result_dict = pywapi.get_weather_from_yahoo(args)
    if not all(result_dict.values()):
        bot.say(channel, 'unknown location')
        return

    def format_day(day):
        return (u'%s: %s (%.0f°C/%.0f°C)' % (day['day_of_week'],
                            day['condition'],
                            fahrenheit_to_celcius(day['low']),
                            fahrenheit_to_celcius(day['high'])))

    answerstr = u'%s: ' % (result_dict['forecast_information']['city'])
    answerstr += u", ".join(format_day(day) for day in result_dict['forecasts'])

    bot.say(channel, answerstr.encode('utf-8'))
