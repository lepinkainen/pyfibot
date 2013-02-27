"""
$Id$
$HeadURL$
"""

from __future__ import unicode_literals, print_function, division
has_imdb = False

try:
    from imdb import IMDb
    has_imdb = True
except:
    print("Could not find IMDbPY library, please install from http://imdbpy.sourceforge.net/")
import re


def command_imdb(bot, user, channel, args):
    pass


def handle_url(bot, user, channel, url, msg):
    """Handle IMDB urls"""
    if not has_imdb:
        return
    m = re.match("http://.*?\.imdb\.com/title/tt([0-9]+)/?", url)
    if not m:
        return

    i = IMDb()
    movie = i.get_movie(m.group(1))
    title = movie['long imdb title']
    rating = movie.get('rating', 0.0)
    votes = movie.get('votes', 'no')
    toprank = movie.get('top 250 rank')
    rank = ""
    if toprank:
        rank = "Top 250: #%d" % toprank
    bottomrank = movie.get('bottom 100 rank')
    if bottomrank:
        rank = "Bottom 100: #%d" % bottomrank

    genre = "(" + "/".join(movie.get('genres')) + ")"

    msg = "[IMDB] %s - Rating: %.1f (%s votes) %s %s" % (title, rating, votes, genre, rank)
    msg = msg.encode("UTF-8")

    return bot.say(channel, msg)
