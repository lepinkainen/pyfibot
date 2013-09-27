# -*- encoding: utf-8 -*-
"""
Get package tracking information from the Finnish postal service
"""

from __future__ import unicode_literals, print_function, division
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta

lang = 'en'


def command_posti(bot, user, channel, args):
    """Parse the package status page"""
    args = args.strip()
    if not args:
        return bot.say(channel, 'Need a tracking ID as argument.')

    url = 'http://www.itella.fi/itemtracking/itella/search_by_shipment_id'

    params = {
        'ShipmentId': args,
        'lang': lang,
        'LOTUS_hae': 'Hae',
        'LOTUS_side': '1'
    }

    r = requests.post(url, params=params)
    bs = BeautifulSoup(r.content)

    try:
        status_table = bs.find('table', {'id': 'shipment-event-table'}).find_all('tr')[1]
    except:
        if lang == 'en':
            return bot.say(channel, 'Item not found.')
        return bot.say(channel, 'Lähetystä ei löytynyt.')

    try:
        event = status_table.find('div', {'class': 'shipment-event-table-header'}).text.strip()
    except:
        event = '???'

    location = '???'
    dt = timedelta(0, 0, 0)
    now = datetime.now()
    for x in status_table.find_all('div', {'class': 'shipment-event-table-row'}):
        try:
            row_label = x.find('span', {'class': 'shipment-event-table-label'}).text.strip()
            row_data = x.find('span', {'class': 'shipment-event-table-data'}).text.strip()
        except:
            continue

        if lang == 'en':
            if row_label == 'Registration:':
                dt = now - datetime.strptime(row_data, '%d.%m.%Y %H:%M:%S')
            if row_label == 'Location:':
                location = row_data
        else:
            if row_label == 'Rekisteröinti:':
                dt = now - datetime.strptime(row_data, '%d.%m.%Y klo %H:%M:%S')
            if row_label == 'Paikka:':
                location = row_data

    agestr = []
    if dt.days > 0:
        agestr.append('%dd' % dt.days)
    secs = dt.seconds
    hours, minutes, seconds = secs // 3600, secs // 60 % 60, secs % 60
    if hours > 0:
        agestr.append('%dh' % hours)
    if minutes > 0:
        agestr.append('%dm' % minutes)

    if lang == 'en':
        return bot.say(channel, '%s - %s - %s' % (' '.join(agestr) + ' ago', event, location))
    return bot.say(channel, '%s - %s - %s' % (' '.join(agestr) + ' sitten', event, location))
