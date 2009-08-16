import re
import urllib

def do_spotify(bot, user, channel, dataurl):    
    f = urllib.urlopen(dataurl)
    songinfo = f.read()
    f.close()

    artist, album, song = songinfo.split("/", 2)

    bot.say(channel, "[Spotify] %s - %s (%s)" % (artist.strip(), song.strip(), album.strip()))

def handle_privmsg(bot, user, reply, msg):
    """Grab Spotify URLs from the messages and handle them"""

    m = re.match("(http:\/\/open.spotify.com\/|spotify:)(album|artist|track)([:\/])([a-zA-Z0-9]+)\/?", msg)
    if not m: return

    dataurl = "http://spotify.url.fi/%s/%s?txt" % (m.group(2), m.group(4))

    do_spotify(bot, user, reply, dataurl)
