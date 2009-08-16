
import re
import urllib

def handle_url(bot, user, channel, url, msg):
    """Handle IMDB urls"""
    
    m = re.match("(http:\/\/open.spotify.com\/|spotify:)(album|artist|track)([:\/])([a-zA-Z0-9]+)\/?", url)
    if not m: return

    dataurl = "http://spotify.url.fi/%s/%s?txt" % (m.group(2), m.group(4))

    f = urllib.urlopen(dataurl)
    songinfo = f.read()
    f.close()

    artist, album, song = songinfo.split("/", 2)

    bot.say(channel, "[Spotify] Artist: %s - Album: %s - Song: %s" % (artist.strip(), album.strip(), song.strip()))
