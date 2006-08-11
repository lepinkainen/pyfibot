# -*- coding: iso-8859-1 -*-
"""IMDB"""

from util.BeautifulSoup import BeautifulSoup
from util.BeautifulSoup import Tag

import re
import urllib
import urlparse
import time

def command_imdb(user, channel, args):
    """Search IMDB for movies. Usage: imdb <name of movie>"""

    say(channel, search(args))

def search(searchterm):
    """Movie title search"""
    # title search

    searchurl = "http://uk.imdb.com/find?q=%s&tv=both&tt=1" % urllib.quote(searchterm)

    d = getUrl(searchurl)
    data = d.getContent()
    realurl = d.fp.geturl()
    
    # search redirected immediately, no need to parse search
    if re.match(".*/title/tt[\d]+/", realurl):
        urls = [realurl]
    else:
        isp = IMDBSearchParser(data)
        urls = isp.getMatches()

    if urls:
        url = urls[0]
        return getSummary(url)
    else:
        return "No results found"

def getSummary(url):
    """Get summary for given movie"""

    data = getUrl(url).getContent()
    
    ip = IMDBMovieParser(data)
    
    res =  "%s (%s) | Genre: %s | Rating: %s" % (ip.getTitle(), ip.getDirector(), ip.getGenre(), ip.getRating())

    # clean up the butt-ugly url from imdb
    t = urlparse.urlparse(url)
    l = list(t)
    l[4] = ''
    url = urlparse.urlunparse(tuple(l))
    
    res = res+" | "+url

    return res

class IMDBSearchParser:
    """Parse IMDB search result page"""
    
    def __init__(self, page):
        self.page = page
        
        self.bs = BeautifulSoup()
        self.bs.feed(self.page)

    def getMatches(self):
        """Get result links from search page"""

        links = self.bs.fetch('a', {'href':re.compile('/title/tt')})

        res = []
        # convert links to absolute urls
        for link in links:
            res.append('http://www.imdb.com%s' % link['href'])

        return res
    
class IMDBMovieParser:
    """Parse IMDB movie info page"""

    def __init__(self, page=None):
        self.page = page

        self.htmlRemove = re.compile('<.*?>')
        
        self.bs = BeautifulSoup()
        
        if page:
            self.bs.feed(self.page)

    def feed(self, data):
        self.bs.feed(data)

    def getTitle(self):
        """Parse title"""

        # this should be pretty foolproof
        title = re.sub(self.htmlRemove, '', str(self.bs.first('strong', {'class':'title'}))).rstrip()

        # KLUDGE
        # replace &#34; with "
        # TODO: Replace these with u'\AWITHDOTS' stuff
        title = title.replace('&#34;',  '"')
        title = title.replace('&#228;', 'ä')
        title = title.replace('&#246;', 'ö')
        
        return title
        
    def getDirector(self):
        """Parse director"""
        #return re.sub(self.htmlRemove, '', str(self.bs.first('b', {'class':'blackcatheader'}).next.next.next.next))
        #return re.sub(self.htmlRemove, '', str(self.bs.first('a', {'href':'/name/%'}).string))
        director = self.bs.fetch(text="Directed by")
        if director:
            return director[0].next.next.next.next.string
        else:
            return None

    def getGenre(self):
        """Parse genre"""

        # find the genre start
        curr = self.bs.first('b', {'class':'ch'}).next.next

        genre = []
        
        while True:
            if not isinstance(curr, Tag):
                genre.append(str(curr))
            else:
                # end on first <br/>
                if curr.name == 'br':
                    if "(more)" in genre: genre.remove('(more)')
                    return "".join(genre).strip()
                    
            curr = curr.next

        return "N/A"

    def getRating(self):
        """Parse rating and number of votes"""

        try:
            rating = self.bs.fetch('img', {'src':re.compile('star.gif')})[-1:][0].next.next.next
        except IndexError:
            # movie has no rating
            return "N/A (N/A votes)"

        votecount = rating.next.string.strip()

        rating = rating.string.split('/')[0].strip()

        return "%s %s" % (rating, votecount)
