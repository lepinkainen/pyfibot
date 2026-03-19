import logging
import socket

import geoip2.database
import geoip2.errors

try:
    from modules.module_usertrack import get_table

    user_track_available = True
except ImportError:
    user_track_available = False

log = logging.getLogger("geoip")
reader = None


def init(botref):
    global reader
    config = botref.config.get("module_geoip", {})
    database = config.get("database", "GeoLite2-Country.mmdb")

    try:
        reader = geoip2.database.Reader(database)
        log.info("Loaded GeoIP2 database from %s", database)
    except FileNotFoundError:
        log.error(
            "GeoIP2 database not found: %s - download GeoLite2-Country.mmdb from MaxMind",
            database,
        )


def command_geoip(bot, user, channel, args):
    """Determine the user's country based on host or nick, if module_usertrack is used."""
    if not args:
        return bot.say(channel, "usage: .geoip HOST/NICK")

    if not reader:
        return bot.say(channel, "GeoIP database not loaded")

    host = args
    nick = None

    if user_track_available:
        table = get_table(bot, channel)
        user = table.find_one(nick=args)
        if user:
            nick = user["nick"]
            host = user["host"]

    try:
        # geoip2 requires an IP address, resolve hostname first
        ip = socket.gethostbyname(host)
        response = reader.country(ip)
        country = response.country.name
    except socket.gaierror:
        country = None
    except geoip2.errors.AddressNotFoundError:
        country = None

    if country:
        if nick:
            return bot.say(channel, "%s (%s) is in %s" % (nick, host, country))
        return bot.say(channel, "%s is in %s" % (host, country))
    if nick:
        return bot.say(channel, "Host not found for %s (%s)" % (nick, host))
    return bot.say(channel, "Host not found for %s" % host)
