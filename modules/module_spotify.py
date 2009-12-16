import re
import urllib

def do_spotify(bot, user, channel, dataurl, type):    
    f = urllib.urlopen(dataurl)
    songinfo = f.read()
    f.close()
    
    if type == "track":
        artist, album, song = songinfo.split("/", 2)
        return bot.say(channel, "[Spotify] %s - %s (%s)" % (artist.strip(), song.strip(), album.strip()))
    elif type == "artist":
        return bot.say(channel, "[Spotify] %s" % songinfo.strip())
    elif type == "album":
        artist, album = songinfo.split("/", 1)
        return bot.say(channel, "[Spotify] %s - %s" % (artist.strip(), album.strip()))
    else:
        return None

def handle_privmsg(bot, user, reply, msg):
    """Grab Spotify URLs from the messages and handle them"""

    m = re.match("(http:\/\/open.spotify.com\/|spotify:)(album|artist|track)([:\/])([a-zA-Z0-9]+)\/?", msg)
    if not m: return None

    dataurl = "http://spotify.url.fi/%s/%s?txt" % (m.group(2), m.group(4))

    return do_spotify(bot, user, reply, dataurl, m.group(2))
