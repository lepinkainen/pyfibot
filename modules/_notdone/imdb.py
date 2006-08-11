#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

"""IMDB Search parsers"""

from util.BeautifulSoup import BeautifulSoup
from util.BeautifulSoup import Tag


# TODO
# Country, Language, Plot Summary

def search(searchterm):
    # title search

    searchurl = "http://uk.imdb.com/find?q=%s&tv=both&tt=1" % urllib.quote(searchterm)

    import time
    start = time.time()
    print "IMDB: Getting search result...",
    f = urllib.urlopen(searchurl)
    data = f.read()
    realurl = f.geturl()
    f.close()
    print "DONE", time.time()-start
    
    # search redirected immediately, no need to parse search
    if re.match(".*/title/tt[\d]+/", realurl):
        urls = [realurl]
    else:
        isp = IMDBSearchParser(data)
        urls = isp.getMatches()

    if urls:
        url = urls[0]
        print "URLLIIIIIAAAAHH", url
        start = time.time()
        print "IMBD: Getting result page (%s)..." % url,
        f = urllib.urlopen(url)
        data = f.read()
        f.close()
        print "DONE", time.time()-start

        start = time.time()
        print "IMDB: Parsing page...",
        ip = IMDBMovieParser(data)
        print "DONE", time.time()-start

        res =  "%s (%s) | Genre: %s | Rating: %s" % (ip.getTitle(), ip.getDirector(), ip.getGenre(), ip.getRating())
        
        if len(urls) > 1:
            res = "Best match: "+res

        res = res+" | "+url

        f.close()
        return res
    else:
        f.close()
        return "No results found"
    

class IMDBSearchParser:
    """Parse IMDB search result page"""
    
    def __init__(self, page):
        self.page = page
        
        self.bs = BeautifulSoup()
        self.bs.feed(self.page)

    def getMatches(self):
        """Get result links from search page"""

        links = self.bs.fetch('a', {'href':'/title/tt%'})

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
        director = self.bs.fetch(contents="Directed by")
        if director:
            return director.[0].next.next.next.next.string
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
            rating = self.bs.fetch('img', {'src':'%star.gif'})[-1:][0].next.next.next
        except IndexError:
            # movie has no rating
            return "N/A (N/A votes)"

        votecount = rating.next.string.strip()

        rating = rating.string.split('/')[0].strip()

        return "%s %s" % (rating, votecount)
