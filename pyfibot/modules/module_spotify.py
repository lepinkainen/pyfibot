"""
$Id$
$HeadURL$
"""

from __future__ import unicode_literals, print_function, division
import re
from BeautifulSoup import BeautifulSoup


def __get_bs(bot, url):
    content = bot.get_url(url).content
    if content:
        return BeautifulSoup(content)
    else:
        return None


def handle_privmsg(bot, user, channel, args):
    """Grab Spotify URLs from the messages and handle them"""

    m = re.match(".*(http:\/\/open.spotify.com\/|spotify:)(album|artist|track)([:\/])([a-zA-Z0-9]+)\/?.*", args)
    if not m:
        return None

    apiurl = "http://ws.spotify.com/lookup/1/?uri=spotify:%s:%s" % (m.group(2), m.group(4))

    bs = __get_bs(bot, apiurl)
    if not bs:
        return

    data = '[Spotify] '
    if m.group(2) == 'album':
        artist = str(bs.first('album').first('artist').first('name').string)
        name = str(bs.first('album').first('name').string)
        year = str(bs.first('album').first('released').string)
        data += '%s - %s (%s)' % (artist, name, year)
    if m.group(2) == 'artist':
        data += str(bs.first('artist').first('name').string)
    if m.group(2) == 'track':
        artist = str(bs.first('track').first('artist').first('name').string)
        #album = str(bs.first('track').first('album').first('name').string)
        title = str(bs.first('track').first('name').string)
        data += '%s - %s' % (artist, title)

    return bot.say(channel, data)
