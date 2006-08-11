"""Reminders & alarms"""

from twisted.internet import reactor

def command_delaysay(user, channel, args):
    """Say something on the current channel with a delay. Usage: delaysay <absolute time or delay> <message>"""

    from util import ptime
    
    delay = args.split(" ", 1)[0]
    args = " ".join(args.split(" ")[1:])

    if not delay: return
    
    delay = ptime.convert(delay)
    nick = getNick(user)
    reactor.callLater(delay, say, channel, "%s: %s" % (nick, args))
    
    say(channel, "%s: OK, will notify you in a while" % (nick))
