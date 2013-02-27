# -*- encoding: utf-8 -*-
from __future__ import unicode_literals, print_function, division


def command_btc(bot, user, channel, args):
    """Display BTC exchange rates"""

    r = bot.get_url("http://bitcoincharts.com/t/weighted_prices.json")
    data = r.json()
    eur_rate = float(data['EUR']['24h'])
    usd_rate = float(data['USD']['24h'])

    return bot.say(channel, "1 BTC = $%.2f / %.2f€" % (usd_rate, eur_rate))
