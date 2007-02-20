"""Displays HTML page titles

Smart title functionality for sites which could have clear titles,
but still decide show idiotic bulk data in the HTML title element"""

import fnmatch
import htmlentitydefs
import urlparse

from types import TupleType

from BeautifulSoup import BeautifulStoneSoup

def handle_url(bot, user, channel, url):
    """Handle urls"""

    if channel == "#wow": return

    handlers = [(h,ref) for h,ref in globals().items() if h.startswith("_handle_")]

    # try to find a specific handler for the URL
    for handler, ref in handlers:
        pattern = ref.__doc__.split()[0]
        if fnmatch.fnmatch(url, pattern):
            title = ref(url)
            if title:
                _title(bot, channel, title, True)
            # handler found, abort
            return

    # multiple matches for single method -version
#     for handler, ref in handlers:
#         patterns = ref.__doc__.split()
#         for pattern in patterns:
#             if fnmatch.fnmatch(url, pattern):
#                 title = ref(user, channel, url)
#                 if title:
#                     _title(channel, title)
#                 return
                        
    bs = getUrl(url).getBS()
    if not bs: return
    
    title = bs.first('title')
    # no title attribute
    if not title: return

    

    try:
        title = title.string.strip().replace("\n", "").replace("\r", "")
        if _check_redundant(url, title):
            _title(bot, channel, title, redundant=True)   
        else:
            _title(bot, channel, title)
    except AttributeError:
        # TODO: Nees a better way to handle this
        # this happens with empty <title> tags
        pass

def _check_redundant(url, title):
    """Returns true if the url already contains everything in the title"""
    
    buf = []
    for ch in url:
        if ch.isalnum(): buf.append(ch)
        url = (''.join(buf)).lower()
    buf = []
    for ch in title:
        if ch.isalnum() or ch == ' ': buf.append(ch)
        title = (''.join(buf)).lower().split()
    for word in title:
        if word not in url: return False

    return True

def _title(bot, channel, title, smart=False, redundant=False):
    """Say title to channel"""

    if smart:
        prefix = "Smart title:"
    else:
        prefix = "Title:"

    if redundant:
        suffix = " [Redundant]"
    else:
        suffix = ""

    info = None
    # tuple, additional info
    if type(title) == TupleType:
        info = title[1]
        title = title[0]
    
    # crop obscenely long titles
    if len(title) > 200:
        title = title[:200]+"..."

    #title = _resolve_entities(title)
    title = BeautifulStoneSoup(title, convertEntities=BeautifulStoneSoup.ALL_ENTITIES)

    if not info:
        bot.say(channel, "%s '%s'%s" % (prefix, title, suffix))
    else:
        bot.say(channel, "%s '%s' %s" % (prefix, title, info))

def _resolve_entities(s):
    for (i, j) in htmlentitydefs.entitydefs.items():
        s = s.replace("&%s;" % i, j)

    return s

##### HANDLERS #####

def _handle_hs(url):
    """*hs.fi*artikkeli*"""
    bs = getUrl(url).getBS()
    if not bs: return
    title = bs.find("title")
    title = title.string.split("-")[0].strip()
    return title

## WORKING 20070209

def _handle_ircquotes(url):
    """*ircquotes.net*"""
    pass

def _handle_verkkokauppa(url):
    """*verkkokauppa.com*"""
    pass

def _handle_wikipedia(url):
    """*wikipedia.org*"""
    pass

def _handle_imageshack(url):
    """*imageshack.us/my.php*"""
    pass

def _handle_mtv3(url):
    """*mtv3.fi*"""
    bs = getUrl(url).getBS()
    title = bs.first("h1", "otsikko").next

    return title

def _handle_iltalehti(url):
    """*iltalehti.fi*html"""

    # go as normal
    bs = getUrl(url).getBS()
    if not bs: return
    title = bs.first('title').string

    # the last part is the actual story title, lose the rest
    title = title.split("|")[-1].strip()

    if not title: return

    return title

def _handle_iltasanomat(url):
    """*iltasanomat.fi*"""
    bs = getUrl(url).getBS()
    if not bs: return

    title = bs.first('h2', {'class':'h2Topic size26'})

    if title:
        title = title.next
        return title

def _handle_kaleva(url):
    """*kaleva.fi*"""
    bs = getUrl(url).getBS()
    if not bs: return

    title = bs.first('span', {'class':'bigheadblk'})

    if title:
        title = title.string
        return title

def _handle_keskisuomalainen_sahke(url):
    """*keskisuomalainen.net*sahkeuutiset/*"""

    bs = getUrl(url).getBS()
    if not bs: return

    title = bs.first('p', {'class':'jotsikko'})

    if title:
        title = title.next.strip()
        return title

def _handle_tietokone(url):
    """http://www.tietokone.fi/uutta/uutinen.asp?news_id=*"""
    bs = getUrl(url).getBS()

    sub = bs.first('span', {'class':'clsHdrTPun'}).next.string
    main = bs.first('span', {'class':'clsHdrMajor'}).next.string

    return "%s - %s" % (main, sub)

def _handle_itviikko(url):
    """http://www.itviikko.fi/page.php*"""

    # <font face="Arial, Helvetica, sans-serif" size="+2">
    bs = getUrl(url).getBS()
    if not bs: return
    title1 = bs.first("h2").next.next
    title2 = title1.next
    return "%s - %s" % (title1, title2)

def _handle_kauppalehti(url):
    """http://www.kauppalehti.fi/4/i/uutiset/*"""
    bs = getUrl(url).getBS()
    if not bs: return

    title = bs.fetch("h1")[1].string.strip("\n ")

    return title

def _handle_verkkokauppa(url):
    """http://www.verkkokauppa.com/popups/prodinfo.php?id=*"""
    bs = getUrl(url).getBS()
    if not bs: return

    return bs.first("td", {'valign':'top', 'width':'59%', 'height':'139'}).next.strip()
