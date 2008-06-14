# -*- coding: utf-8 -*-
"""Displays HTML page titles

Smart title functionality for sites which could have clear titles,
but still decide show idiotic bulk data in the HTML title element"""

import fnmatch
import htmlentitydefs
import urlparse
import re

from types import TupleType

from BeautifulSoup import BeautifulStoneSoup

def init(botconfig):
    global config
    config = botconfig["module_urltitle"]

def handle_url(bot, user, channel, url, msg):
    """Handle urls"""

    if msg.startswith("-"): return

    if channel == "#wow": return
    if channel == "#debian.fi" and not "youtube" in url: return

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

    prefix = "Title:"

    if False:
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

    title = BeautifulStoneSoup(title, convertEntities=BeautifulStoneSoup.ALL_ENTITIES)
    print title

    if not info:
        bot.say(channel, "%s '%s'%s" % (prefix, title, suffix))
    else:
        bot.say(channel, "%s '%s' %s" % (prefix, title, info))

##### HANDLERS #####

def _handle_hs(url):
    """*hs.fi*artikkeli*"""
    bs = getUrl(url).getBS()
    if not bs: return
    title = bs.title.string
    title = title.split("-")[0].strip()
    return title

## WORKING 20070209

def _handle_ircquotes(url):
    """*ircquotes.net*"""
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

    # the first part is the actual story title, lose the rest
    title = title.split("|")[0].strip()

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

    sub = bs.first('h5').string
    main = bs.first('h2').string

    return "%s - %s" % (main, sub)

def _handle_itviikko(url):
    """http://www.itviikko.fi/*/*/*/*/*"""

    bs = getUrl(url).getBS()
    if not bs: return
    return bs.first("h1", "headline").string

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

    product = bs.first("td", {'valign':'top', 'width':'59%', 'height':'139'}).next.strip()
    price = str(bs.first(text="Hinta:").next.next.next.next.string).split("&")[0]

    return "%s | %s EUR" % (product, price)


def _handle_yle(url):
    """http://*yle.fi/uutiset/*"""
    bs = getUrl(url).getBS()
    if not bs: return

    title = bs.first("font", {'size':'3'}).next.string

    return title

def _handle_mol(url):
    """http://www.mol.fi/paikat/Job.do?*"""
    bs = getUrl(url).getBS()
    if not bs: return

    title = bs.first("div", {'class':'otsikko'}).string

    return title

def _handle_youtube_gdata(url):
    """http://*youtube.com/watch?v=*"""
    gdata_url = "http://gdata.youtube.com/feeds/api/videos/%s"
    
    match = re.match("http://.*?youtube.com/watch\?v=([^&]+)", url)
    if match:
        infourl = gdata_url % match.group(1)
        print infourl
        bs = getUrl(infourl).getBS()
    
        entry = bs.first("entry")
        author = entry.author.next.string
        # if an entry doesn't have a rating, the whole element is missing
        try:
            rating = float(entry.first("gd:rating")['average'])
        except TypeError:
            rating = 0.0

        stars = int(round(rating)) * "*"
            
        views = entry.first("yt:statistics")['viewcount']

        racy = entry.first("yt:racy")

        media = entry.first("media:group")
        title = media.first("media:title").string
        secs = int(media.first("yt:duration")['seconds'])

        lengthstr = []
        hours,minutes,seconds = secs//3600,secs//60%60,secs%60

        if hours > 0: lengthstr.append("%dh" % hours)
        if minutes > 0: lengthstr.append("%dm" % minutes)
        if seconds > 0: lengthstr.append("%ds" % seconds)

        if racy:
            adult = " - XXX"
        else:
            adult = ""
        
        return "%s by %s [%s - %s - %s views%s]" % (title, author, "".join(lengthstr), "[%-5s]" % stars, views, adult)
