# -*- coding: utf-8 -*-
"""
Koronavirus statistics from HS.fi open data
https://github.com/HS-Datadesk/koronavirus-avoindata
"""

from __future__ import unicode_literals, print_function, division
from collections import Counter
from datetime import datetime, date
import dateutil.parser

def init(bot):
    global lang
    config = bot.config.get("module_posti", {})
    lang = config.get("language", "en")


def command_korona(bot, user, channel, args):
    """Get latest info about COVID-19 in Finland (Source: https://github.com/HS-Datadesk/koronavirus-avoindata )"""
    url = "https://w3qa5ydb4l.execute-api.eu-west-1.amazonaws.com/prod/finnishCoronaData"
    try:
        r = bot.get_url(url)
        data = r.json()
    except Exception as e:
        bot.say(
            channel,
            "Error while getting data from API",
        )
        raise e


    today_confirmed = len(list(filter(lambda x: dateutil.parser.parse(x['date']).date() == date.today(), data['confirmed'])))
    today_deaths = len(list(filter(lambda x: dateutil.parser.parse(x['date']).date() == date.today(), data['deaths'])))
    today_recovered = len(list(filter(lambda x: dateutil.parser.parse(x['date']).date() == date.today(), data['recovered'])))

    display = {
      'confirmed': len(data['confirmed']),
      'deaths': len(data['deaths']),
      'today_confirmed': today_confirmed,
      'today_deaths': today_deaths
    }

    msg = "[COVID-19 SUOMESSA]"
    msg += " Vahvistettuja tapauksia: {confirmed} (+{today_confirmed}), Kuolleita: {deaths} (+{today_deaths})".format(**display)


    # top5 infection sources
    top5 = Counter(map(lambda x: x['infectionSourceCountry'], data['confirmed'])).most_common(5)

    topstr = []
    for country, count in top5:
        if country is None:
            country = "N/A"

        topstr.append(country + ":" + str(count))

    #msg = msg + | Top5 lähdemaat: " + " ".join(topstr)

    bot.say(channel, msg)