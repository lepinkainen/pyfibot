"""
Display webchat users' actual hostnames on join and when requested
"""

from __future__ import unicode_literals, print_function, division
import socket


def handle_userJoined(bot, user, channel):
    nick = getNick(user)
    userhost = user.split("!")[1]
    username, host = userhost.split("@")
    username = username.replace("~", "").replace("-", "")
    # known webchat hosts
    if host in ["webchat.xs4all.nl", "wwwirc.kapsi.fi", "webchat.mibbit.com", "gateway/web/freenode", "webchat.ircnet.net"] or host.endswith('.kiwiirc.com'):
        origin = webchat_getorigin(username)
        if origin:
            return bot.say(channel, "%s is using webchat from %s" % (nick, origin))


def command_webchat(bot, user, channel, args):
    """Parse a webhcat hex ip to a domain"""
    origin = webchat_getorigin(args)
    if origin:
        return bot.say(channel, "webchat from %s" % origin)
    else:
        return bot.say(channel, "%s: %s is not a valid webchat hex ip" % (getNick(user), args))


def webchat_getorigin(hexip):
    """Parse webchat hex-format ip to decimal ip and hostname if it exists"""
    if len(hexip) != 8:
        return
    ip = []
    for i in range(2, len(hexip) + 2, 2):
        try:
            dec = int(hexip[i - 2:i], 16)
        except ValueError:
            return
        ip.append(str(dec))
    if ip:
        origin = '.'.join(ip)
        hostname = socket.getfqdn(origin)
        if hostname != origin:
            origin = "%s -> %s" % (origin, hostname)
    return origin
