# -*- encoding: utf-8 -*-
"""
Get status of a shipment from DHL Track & Trace service. Experimental.
"""

from __future__ import unicode_literals
from datetime import datetime, timedelta
from bs4 import BeautifulSoup


def command_dhl(bot, user, channel, args):
    """Get latest status of a shipment by DHL shipment number"""

    payload = {'lang': 'en', 'idc': args}
    url = 'https://nolp.dhl.de/nextt-online-public/set_identcodes.do'
    r = bot.get_url(url, params=payload)
    bs = BeautifulSoup(r.content)

    status_div = bs.find('div', {'class': 'accordion-inner'})
    if status_div:
        status_table = status_div.find('tbody')
    else:
        return bot.say(channel, "Shipment with that number does not exist or an error occurred.")
    status_row = None

    for row in status_table.find_all('tr'):
        try:
            status_row = row.find_all('td')
        except:
            continue

    date_str = status_row[0].text.strip()
    place = status_row[1].text.strip()
    status = status_row[2].text.strip()
    dt = datetime.now() - datetime.strptime(date_str[5:], '%d.%m.%Y %H:%M h')

    next_step = bs.find('td', text='Next step')
    if next_step:
        status += ' - Next step: %s' % next_step.next.next.next.next.strip()

    agestr = []
    if dt.days > 0:
        agestr.append('%dd' % dt.days)
    secs = dt.seconds
    hours, minutes, seconds = secs // 3600, secs // 60 % 60, secs % 60
    if hours > 0:
        agestr.append('%dh' % hours)
    if minutes > 0:
        agestr.append('%dm' % minutes)

    return bot.say(channel, '%s - %s - %s' % (' '.join(agestr) + ' ago', place, status))
