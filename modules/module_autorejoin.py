# rejoin after 1 minute
delay = 60

from twisted.internet import reactor

def handle_kickedFrom(bot, channel, kicker, message):
    """Rejoin channel after 60 seconds"""
    
    bot.log("Kicked by %s from %s. Reason: %s" % (kicker, channel, message))
    bot.log("Rejoining in %d seconds" % delay)

    bot.network.channels.remove(channel)
    
    reactor.callLater(delay, bot.join, channel)
