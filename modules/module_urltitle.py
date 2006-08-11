"""Displays HTML page titles

Smart title functionality for sites which could have clear titles,
but still decide show idiotic bulk data in the HTML title element"""

import fnmatch
import htmlentitydefs
import urlparse

from types import TupleType

def handle_url(bot, user, channel, url):
    """Handle urls"""

    handlers = [(h,ref) for h,ref in globals().items() if h.startswith("_handle_")]

    # try to find a specific handler for the URL
    for handler, ref in handlers:
        pattern = ref.__doc__.split()[0]
        if fnmatch.fnmatch(url, pattern):
            title = ref(user, channel, url)
            if title:
                _title(bot, channel, title, True)
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
        _title(bot, channel, title)
    except AttributeError:
        # TODO: Nees a better way to handle this
        # this happens with empty <title> tags
        pass

def _title(bot, channel, title, smart=False):
    """Say title to channel"""

    if smart:
        prefix = "Smart title:"
    else:
        prefix = "Title:"

    info = None
    # tuple, additional info
    if type(title) == TupleType:
        info = title[1]
        title = title[0]
    
    # crop obscenely long titles
    if len(title) > 200:
        title = title[:200]+"..."

    title = _resolve_entities(title)

    if not info:
        bot.say(channel, "%s '%s'" % (prefix, title))
    else:
        bot.say(channel, "%s '%s' %s" % (prefix, title, info))

def _resolve_entities(s):
    for (i, j) in htmlentitydefs.entitydefs.items():
        s = s.replace("&%s;" % i, j)

    return s

def _handle_tunnustustenluola(user, channel, url):
    """*tunnustusten.luola.net*"""
    pass

def _handle_tunnustuksienluola(user, channel, url):
    """*tunnustuksien.luola.net*"""
    pass

def _handle_ircquotes(user, channel, url):
    """*ircquotes.net*"""
    pass

def _handle_verkkokauppa(user, channel, url):
    """*verkkokauppa.com*"""
    pass

def _handle_bdog(user, channel, url):
    """*www.bdog.fi*"""
    pass

def _handle_keskisuomalainen_sahke(user, channel, url):
    """*keskisuomalainen.net*sahkeuutiset/*"""

    bs = getUrl(url).getBS()
    if not bs: return

    title = bs.first('span', {'class':'jotsikko'})
    if not title:
        title = bs.first('p', {'class':'jotsikko'})

    if title:
        title = title.next.string.split('\n')[2]
        title = title.strip()
        return title

# http://www.iltasanomat.fi/uutiset/sahkeet.asp?id=854870
def _handle_iltasanomat(user, channel, url):
    """*iltasanomat.fi*sahkeet*"""
    bs = getUrl(url).getBS()
    if not bs: return

    title = bs.first('span', {'class':'otsikko'})

    if title:
        title = title.string
        return title

def _handle_kaleva(user, channel, url):
    """*kaleva.fi*"""
    bs = getUrl(url).getBS()
    if not bs: return

    title = bs.first('span', {'class':'bigheadblk'})

    if title:
        title = title.string
        return title

def _handle_iltalehti(user, channel, url):
    """*iltalehti.fi*html"""

    # go as normal
    bs = getUrl(url).getBS()
    if not bs: return
    title = bs.first('title').string

    # the last part is the actual story title, lose the rest
    title = title.split("|")[-1].strip()

    if not title: return

    return title

def _handle_bash(user, channel, url):
    """*bash.org*"""
    pass

def _handle_wikipedia(user, channel, url):
    """*wikipedia.org*"""
    pass

def _handle_nettiauto(user, channel, url):
    """*nettiauto.com*"""
    pass

def _handle_demi(user, channel, url):
    """*demi.fi/keskustelu.php*"""
    bs = getUrl(url).getBS()
    if not bs: return
    title = bs.first("div", {'id':'mamsgsubj'}).next

    return title    

def _handle_itviikko(user, channel, url):
    """http://www.itviikko.fi/uutiset/uutisalue.asp*"""

    # <font face="Arial, Helvetica, sans-serif" size="+2">
    bs = getUrl(url).getBS()
    if not bs: return
    title = bs.first('font',{'face':'Arial, Helvetica, sans-serif', 'size':'+2'}).next.next
    return title

def _handle_thesun(user, channel, url):
    """http://www.thesun.co.uk/article/*"""
    # go as normal
    bs = getUrl(url).getBS()
    if not bs: return
    title = bs.first('span','black24').next

    return title

def _handle_imageshack(user, channel, url):
    """*imageshack.us/my.php*"""
    pass

def _handle_wowforums(user, channel, url):
    """*forums-en.wow-europe.com*"""
    bs = getUrl(url).getBS()
    if not bs: return
    title = bs.first('title').string + bs.first('b', {'class':'white'}).string
    return title

def _handle_wowforums_us(user, channel, url):
    """*forums.worldofwarcraft.com*"""
    bs = getUrl(url).getBS()
    if not bs: return
    title = bs.first('title').string + bs.first('b', {'class':'white'}).string
    return title

def _handle_allakhazam(user, channel, url):
    """http://wow.allakhazam.com/db/item.html?witem=*"""
    try:
        itemId = urlparse.urlsplit(url)[3].split("=")[1]
    except:
        return

    itemUrl = "http://wow.allakhazam.com/ihtml?"+itemId

    bs = getUrl(itemUrl).getBS()

    itemname = bs.first('span', {'class':'iname'}).next.string

    return "%s - %s " % (itemname, itemUrl)

def _handle_tietokone(user, channel, url):
    """http://www.tietokone.fi/uutta/uutinen.asp?news_id=*"""
    bs = getUrl(url).getBS()

    sub = bs.first('span', {'class':'clsHdrTPun'}).next.string
    main = bs.first('span', {'class':'clsHdrMajor'}).next.string

    return "%s - %s" % (main, sub)

