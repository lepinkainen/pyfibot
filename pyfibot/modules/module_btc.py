# -*- encoding: utf-8 -*-
from __future__ import unicode_literals, print_function, division


def command_btc(bot, user, channel, args):
    """Display current BTC exchange rates from mtgox. Usage: btc [whitespace separated list of currency codes]"""
    currencies = ["EUR"]

    if args:
        currencies = args.split(" ")

    rates = []

    for currency in currencies:
        rate = gen_string(bot, currency)
        if rate:
            rates.append(rate)

    if rates:
        return bot.say(channel, "1 BTC = %s" % " | ".join(rates))


def gen_string(bot, currency):
    r = bot.get_url("http://data.mtgox.com/api/1/BTC%s/ticker" % currency)

    if r.json()['result'] != 'success':
        return None

    data = r.json()['return']

    avg  = data['avg']['display_short']
    low  = data['low']['display_short']
    high = data['high']['display_short']
    vol = data['vol']['display_short']

    return "%s avg:%s low:%s high:%s vol:%s" % (currency.upper(), avg, low, high, vol)
