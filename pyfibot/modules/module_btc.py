# -*- encoding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import logging

log = logging.getLogger("mtgox")


def command_bsbtc(bot, user, channel, args):
    """Display current BTC exchange rates from bitstamp"""
    r = bot.get_url("https://www.bitstamp.net/api/ticker/")
    try:
        j = r.json()
    except AttributeError:
        print r.text
        return

    return bot.say(channel, "BitStamp: bid:$%s last:$%s low:$%s high:$%s vol:%s" % (j['bid'], j['last'], j['low'], j['high'], j['volume']))


def command_btc(bot, user, channel, args):
    """Display current BTC exchange rates from mtgox. Usage: btc [whitespace separated list of currency codes]"""
    currencies = ["EUR"]

    if args:
        currencies = args.split(" ")

    value = _get_coin_value(bot, "BTC", currencies)
    if value:
        return bot.say(channel, "MtGox: %s" % value)
    log.debug('Failed to fetch value with currencies "%s"' % args)
    return bot.say(channel, 'Failed to fetch BTC value.')


def _get_coin_value(bot, coin, currencies):

    rates = []

    for currency in currencies:
        rate = _gen_string(bot, coin, currency)
        if rate:
            rates.append(rate)

    if rates:
        return " | ".join(rates)
    else:
        return None


def _gen_string(bot, coin="BTC", currency="EUR"):
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
