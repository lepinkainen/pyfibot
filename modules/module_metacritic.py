"""Metacritic search"""

import urllib # for argument escaping
import re

def command_meta(bot, user, channel, args):
    """Search metacritic for movies, games or music. Usage: meta <searchterms>"""
        
    res = _search(args)
    
    if res:
        print res

        bot.say(channel, "%(name)s: critic: %(score)s (%(reviewcount)s reviews) user: %(userscore)s - %(url)s" % res)
    else:
        bot.say(channel, "No Metacritic matches for '%s'" % args)

def _search(searchterm):
    """Returns the first 10 matches from metacritic"""
    matches = _parse_search(searchterm)
    return _parse_matches(matches)

def _parse_search(term):
    """Search for the given term in metacritic

    @return a list of result urls
    """
    
    url = "http://www.metacritic.com/search/process?ts=%s&ty=0" % (urllib.quote(term))

    bs = getUrl(url).getBS()

    res = [url['href'] for url in bs.fetch('a', {'href': re.compile('http://www.metacritic.com/(video|film|music|games)/')})]

    return res

def _parse_matches(matches):
    """Parse scores from matching pages"""

    count = 0

    for url in matches:

        bs = getUrl(url).getBS()
        
        name = bs.first('title').contents[0].string
        name = name.split(":")[0]
        try:
            score = bs.fetch('img', {'src': re.compile('/_images/scores/'), 'alt': re.compile("Metascore")})[0]['alt'].split(":")[1].strip()
        except KeyError:
            score = "N/A"

        try:
            userscore = bs.fetch('td', {'class':'green'})[0].string
        except:
            userscore = "N/A"

        # number of reviews
        reviewcount = len(bs.fetch('div', {'class':'scoreandreview'}))
        
        res = {}
        res['name'] = name
        res['score'] = score
        res['userscore'] = userscore
        res['reviewcount'] = reviewcount
        res['url'] = url
    
        return res

    return None
