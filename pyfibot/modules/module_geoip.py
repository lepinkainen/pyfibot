from __future__ import unicode_literals, print_function, division
import pygeoip
import os.path
import sys
import socket

try:
    from modules.module_usertrack import get_table
    user_track_available = True
except ImportError:
    user_track_available = False


# http://dev.maxmind.com/geoip/legacy/geolite/
DATAFILE = os.path.join(sys.path[0], "GeoIP.dat")

# STANDARD = reload from disk
# MEMORY_CACHE = load to memory
# MMAP_CACHE = memory using mmap
gi4 = pygeoip.GeoIP(DATAFILE, pygeoip.MEMORY_CACHE)


def command_geoip(bot, user, channel, args):
    """Determine the user's country based on host or nick, if module_usertrack is used."""
    if not args:
        return bot.say(channel, 'usage: .geoip HOST/NICK')

    host = args
    nick = None

    if user_track_available:
        table = get_table(bot, channel)
        user = table.find_one(nick=args)
        if user:
            nick = user['nick']
            host = user['host']

    try:
        country = gi4.country_name_by_name(host)
    except socket.gaierror:
        country = None

    if country:
        if nick:
            return bot.say(channel, "%s (%s) is in %s" % (nick, host, country))
        return bot.say(channel, "%s is in %s" % (host, country))
    if nick:
        return bot.say(channel, 'Host not found for %s (%s)' % (nick, host))
    return bot.say(channel, 'Host not found for %s' % host)
