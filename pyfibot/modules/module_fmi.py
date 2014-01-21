# -*- encoding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from math import isnan

global api_key
global default_place
default_place = 'Helsinki'
api_key = 'c86a0cb3-e0bf-4604-bfe9-de3ca92e0afc'

# Time format for the API
TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
# t2m = temperature, ws_10min = wind speed (10 min avg), rh == relative humidity
PARAMETERS = ['t2m', 'ws_10min', 'rh']


def init(bot):
    global api_key
    global default_place
    config = bot.config.get("module_fmi", {})
    default_place = config.get('default_place', default_place)
    api_key = config.get('api_key', api_key)


def command_saa(bot, user, channel, args):
    ''' Command to fetch data from FMI '''
    global api_key
    global default_place

    if args:
        place = args
    else:
        place = default_place

    starttime = (datetime.utcnow() - timedelta(minutes=10)).strftime(TIME_FORMAT) + 'Z'
    params = {
        'request': 'getFeature',
        'storedquery_id': 'fmi::observations::weather::timevaluepair',
        'parameters': ','.join(PARAMETERS),
        'crs': 'EPSG::3067',
        'place': place,
        'maxlocations': 1,
        'starttime': starttime
    }

    r = bot.get_url('http://data.fmi.fi/fmi-apikey/%s/wfs' % api_key, params=params)
    bs = BeautifulSoup(r.text)

    # Get FMI name, gives the observation place more accurately
    try:
        place = bs.find('gml:name').text
    except AttributeError:
        return bot.say(channel, 'Paikkaa ei löytynyt.')

    # Loop through measurement time series -objects and gather values
    values = {}
    for mts in bs.find_all('wml2:measurementtimeseries'):
        # Get the identifier from mts-tag
        target = mts['gml:id'].split('-')[-1]
        # Get last value from measurements (always sorted by time)
        value = float(mts.find_all('wml2:value')[-1].text)
        # NaN is returned, if observation doesn't exist
        if not isnan(value):
            values[target] = value

    # Build text from values found
    text = []
    if 't2m' in values:
        text.append('lämpötila: %.1f°C' % values['t2m'])
    if 't2m' in values and 'ws_10min' in values:
        # Calculate "feels like" if both temperature and wind speed were found
        feels_like = 13.12 + 0.6215 * values['t2m'] - 13.956 * (values['ws_10min'] ** 0.16) + 0.4867 * values['t2m'] * (values['ws_10min'] ** 0.16)
        text.append('tuntuu kuin: %.1f°C' % feels_like)
    if 'ws_10min' in values:
        text.append('tuulen nopeus: %i m/s' % round(values['ws_10min']))
    if 'rh' in values:
        text.append('ilman kosteus: %i%%' % round(values['rh']))

    # Return place and values to the channel
    return bot.say(channel, '%s: %s' % (place, ', '.join(text)))


def command_keli(bot, user, channel, args):
    ''' Alias for command "saa" '''
    return command_saa(bot, user, channel, args)
