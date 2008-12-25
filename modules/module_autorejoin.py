# rejoin after 1 minute
delay = 60

from twisted.internet import reactor

def handle_kickedFrom(bot, channel, kicker, message):
    """Rejoin channel after 60 seconds"""
    
    bot.log("Kicked by %s from %s. Reason: %s" % (kicker, channel, message))
    bot.log("Rejoining in %d seconds" % delay)

    print bot.network
    print bot.network.channels
    bot.network.channels.remove(channel)
    print bot.network
    print bot.network.channels
    
    reactor.callLater(delay, bot.join, channel)
