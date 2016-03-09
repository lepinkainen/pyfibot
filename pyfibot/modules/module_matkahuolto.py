# -*- encoding: utf-8 -*-
"""
Get consignment tracking info from Matkahuolto
"""

from __future__ import unicode_literals, print_function, division
from datetime import datetime
from bs4 import BeautifulSoup


def init(bot):
    global lang
    config = bot.config.get('module_matkahuolto', {})
    lang = config.get('language', 'en')


def command_mh(bot, user, channel, args):
    """Get latest consignment status from Matkahuolto Track & Trace service"""
    params = {'package_code': args}

    url = 'https://www.matkahuolto.fi/%s/seuranta/tilanne/' % lang

    try:
        r = bot.get_url(url, params=params)
        r.raise_for_status()
        bs = BeautifulSoup(r.content)

        events = bs.select('.events-table table tbody tr')
        if not events:
            alert = bs.select('.tracker-status .alert')[0].get_text(strip=True)
            return bot.say(channel, alert)

    except Exception as e:
        bot.say('Error while getting tracking data. Check the tracking ID or try again later.')
        raise e

    latest_event = events[0].select('td')

    datestr = latest_event[0].get_text(strip=True)
    status = latest_event[1].get_text(strip=True)
    place = latest_event[2].stripped_strings.next()

    dt = datetime.now() - datetime.strptime(datestr, '%d.%m.%Y, %H:%M')

    agestr = []
    if dt.days > 0:
        agestr.append('%dd' % dt.days)
    secs = dt.seconds
    hours, minutes = secs // 3600, secs // 60 % 60
    if hours > 0:
        agestr.append('%dh' % hours)
    if minutes > 0:
        agestr.append('%dm' % minutes)

    ago = '%s %s' % (' '.join(agestr), {'fi': 'sitten', 'sv': 'sedan', 'en': 'ago'}[lang])

    return bot.say(channel, ' - '.join([ago, status, place]))
