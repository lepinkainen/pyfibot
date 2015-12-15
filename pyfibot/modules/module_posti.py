"""
Get shipment tracking info from Posti
"""

from __future__ import unicode_literals, print_function, division
from datetime import datetime, timedelta
from urllib import quote_plus


def init(bot):
    global lang
    config = bot.config.get('module_posti', {})
    lang = config.get('language', 'en')


def parse_timestamp(timestamp):
    return datetime.strptime(timestamp[0:19], '%Y-%m-%dT%H:%M:%S')


def command_posti(bot, user, channel, args):
    """Get latest tracking event for a shipment from Posti. Usage: .posti JJFI00000000000000"""

    if not args:
        return bot.say(channel, 'Tracking ID is required.')

    url = 'http://www.posti.fi/henkiloasiakkaat/seuranta/api/shipments/%s' % quote_plus(args)

    try:
        r = bot.get_url(url)
        r.raise_for_status()
        data = r.json()
        shipment = data['shipments'][0]
    except Exception as e:
        bot.say(channel, 'Error while getting tracking data. Check the tracking ID or try again later.')
        raise e

    phase = shipment['phase']
    eta_timestamp = shipment.get('estimatedDeliveryTime')
    latest_event = shipment['events'][0]

    dt = datetime.utcnow() - parse_timestamp(latest_event['timestamp'])

    agestr = []
    if dt.days > 0:
        agestr.append('%dd' % dt.days)
    secs = dt.seconds
    hours, minutes, seconds = secs // 3600, secs // 60 % 60, secs % 60
    if hours > 0:
        agestr.append('%dh' % hours)
    if minutes > 0:
        agestr.append('%dm' % minutes)

    ago = '%s %s' % (' '.join(agestr), {'fi': 'sitten', 'sv': 'sedan', 'en': 'ago'}[lang])
    description = latest_event['description'][lang]
    location = '%s %s' % (latest_event['locationCode'], latest_event['locationName'])

    msg = ' - '.join([ago, description, location])

    if phase != 'DELIVERED' and eta_timestamp:
        eta_dt = parse_timestamp(eta_timestamp)
        eta_txt = eta_dt.strftime('%d.%m.%Y %H:%M')
        msg = 'ETA %s - %s' % (eta_txt, msg)

    bot.say(channel, msg)
