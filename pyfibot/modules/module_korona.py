# -*- coding: utf-8 -*-
"""
Koronavirus statistics from HS.fi open data
https://github.com/HS-Datadesk/koronavirus-avoindata
"""

from __future__ import unicode_literals, print_function, division
from collections import Counter


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
            "Error while getting data.",
        )
        raise e

    msg = "[COVID-19] Vahvistettuja tapauksia: %s Kuolleita: %s Parantunut: %s" % (len(data['confirmed']), len(data['deaths']), len(data['recovered']))

    # top5 infection sources
    top5 = Counter(map(lambda x: x['infectionSourceCountry'], data['confirmed'])).most_common(5)

    msg = msg + " | Top5 lähdemaat: "

    topstr = []
    for country, count in top5:
        if country is None:
            country = "N/A"

        topstr.append(country + ":" + str(count))

    msg = msg + " ".join(topstr)

    bot.say(channel, msg)
