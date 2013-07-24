"""
"""
from __future__ import unicode_literals, print_function, division

# rejoin after 1 minute
delay = 61

from twisted.internet import reactor


def handle_kickedFrom(bot, channel, kicker, message):
    """Rejoin channel after 60 seconds"""
    try:
        message = message.decode('utf-8')
    except UnicodeDecodeError:
        try:
            message = message.decode('iso-8859-15')
        except UnicodeDecodeError:
            message = "unknown (UnicodeDecodeError)"
    bot.log("Kicked by %s from %s. Reason: %s" % (kicker, channel, message))
    bot.log("Rejoining in %d seconds" % delay)
    bot.network.channels.remove(channel)
    reactor.callLater(delay, bot.join, channel)
