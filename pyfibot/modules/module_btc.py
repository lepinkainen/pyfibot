# -*- encoding: utf-8 -*-
from __future__ import unicode_literals, print_function, division


def command_btc(bot, user, channel, args):
    """Display current BTC exchange rates from mtgox"""

    r = bot.get_url("http://data.mtgox.com/api/1/BTCUSD/ticker")
    btcusd = r.json()['return']['avg']['display_short']
    r = bot.get_url("http://data.mtgox.com/api/1/BTCEUR/ticker")
    btceur = r.json()['return']['avg']['display_short']

    return bot.say(channel, "1 BTC = %s / %s" % (btcusd, btceur))
