# -*- encoding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import logging

log = logging.getLogger("mtgox")


def command_btc(bot, user, channel, args):
    """Display current BTC exchange rates from mtgox. Usage: btc [whitespace separated list of currency codes]"""
    currencies = ["EUR"]

    if args:
        currencies = args.split(" ")

    value = get_coin_value(bot, "BTC", currencies)
    if value:
        return bot.say(channel, value)
    log.debug('Failed to fetch value with currencies "%s"' % args)
    return bot.say(channel, 'Failed to fetch BTC value.')


def command_ltc(bot, user, channel, args):
    """Display current LTC exchange rates from mtgox. Usage: ltc [whitespace separated list of currency codes]"""
    currencies = ["EUR"]

    if args:
        currencies = args.split(" ")

    value = get_coin_value(bot, "LTC", currencies)
    if value:
        return bot.say(channel, value)
    log.debug('Failed to fetch value with currencies "%s"' % args)
    return bot.say(channel, 'Failed to fetch LTC value.')


def get_coin_value(bot, coin, currencies):

    rates = []

    for currency in currencies:
        rate = gen_string(bot, coin, currency)
        if rate:
            rates.append(rate)

    if rates:
        return "1 %s = %s" % (coin, " | ".join(rates))
    else:
        return None


def gen_string(bot, coin="BTC", currency="EUR"):
    r = bot.get_url("http://data.mtgox.com/api/2/%s%s/money/ticker" % (coin, currency.upper()))

    if r.json()['result'] != 'success':
        log.warn("API call failed:")
        log.warn(r.text)
        return None

    data = r.json()['data']

    avg = data['avg']['display_short']
    low = data['low']['display_short']
    high = data['high']['display_short']
    vol = data['vol']['display_short']

    return "%s avg:%s low:%s high:%s vol:%s" % (currency.upper(), avg, low, high, vol)
