
from imdb import IMDb
import re

def handle_url(bot, user, channel, url, msg):
    """Handle urls"""

    m = re.match("http://.*?\.imdb\.com/title/tt([0-9]+)/", url)

    if not m: return
    
    
    i = IMDb()
    movie = i.get_movie(m.group(1))

    title = movie['long imdb title']
    rating = movie.get('rating', 0.0)
    votes = movie.get('votes', 'no')

    msg = "[IMDB] %s - Rating: %.1f (%s votes)" % (title, rating, votes)
    print msg
    msg = str(msg)
    bot.say(channel, msg)
