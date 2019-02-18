"""
"""
from __future__ import unicode_literals, print_function, division
from twisted.internet import reactor

# rejoin after 1 minute
delay = 61


def handle_kickedFrom(bot, channel, kicker, message):
    """Rejoin channel after 60 seconds"""
    bot.log("Kicked by %s from %s. Reason: %s" % (kicker, channel, message))
    bot.log("Rejoining in %d seconds" % delay)
    bot.network.channels.remove(channel)
    # pylint: disable=no-member
    reactor.callLater(delay, bot.join, channel)
