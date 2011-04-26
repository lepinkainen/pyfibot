# -*- coding: utf-8 -*-
"""Displays HTML page titles

Smart title functionality for sites which could have clear titles,
but still decide show idiotic bulk data in the HTML title element"""

import fnmatch
import htmlentitydefs
import urlparse
import logging
import re
import json

from types import TupleType

from util.BeautifulSoup import BeautifulStoneSoup

log = logging.getLogger("urltitle")

def init(bot):
    global config
    config = bot.config.get("module_urltitle", {})

def handle_url(bot, user, channel, url, msg):
    """Handle urls"""

    if msg.startswith("-"): return
    if re.match("http://.*?\.imdb\.com/title/tt([0-9]+)/?", url): return # IMDB urls are handled elsewhere
    if re.match("(http:\/\/open.spotify.com\/|spotify:)(album|artist|track)([:\/])([a-zA-Z0-9]+)\/?", url): return # spotify handled elsewhere

    if channel.lstrip("#") in config.get('disable', ''): return

    # hack, support both ignore and ignore_urls for a while
    for ignore in config.get("ignore", []):
        if fnmatch.fnmatch(url, ignore): 
            log.info("Ignored URL: %s %s", url, ignore)
            return
    for ignore in config.get("ignore_urls", []):
        if fnmatch.fnmatch(url, ignore): 
            log.info("Ignored URL: %s %s", url, ignore)
            return
    for ignore in config.get("ignore_users", []):
        if fnmatch.fnmatch(user, ignore): 
            log.info("Ignored url from user: %s, %s %s", user, url, ignore)
            return

    # a crude way to handle the new-fangled shebang urls as per
    # http://code.google.com/web/ajaxcrawling/docs/getting-started.html
    # this can manage twitter + gawker sites for now
    url = url.replace("#!", "?_escaped_fragment_=")

    handlers = [(h,ref) for h,ref in globals().items() if h.startswith("_handle_")]

    # try to find a specific handler for the URL
    for handler, ref in handlers:
        pattern = ref.__doc__.split()[0]
        if fnmatch.fnmatch(url, pattern):
            title = ref(url)
            if title:
                # handler found, abort
                return _title(bot, channel, title, True)
                        
    bs = getUrl(url).getBS()
    if not bs: return
    
    title = bs.first('title')
    # no title attribute
    if not title: return

    try:
        # remove trailing spaces, newlines, linefeeds and tabs
        title = title.string.strip()
        title = title.replace("\n", " ")
        title = title.replace("\r", " ")
        title = title.replace("\t", " ")

        # compress multiple spaces into one
        title = re.sub("[ ]{2,}", " ", title)

        # nothing left in title (only spaces, newlines and linefeeds)
        if not title: return

        if _check_redundant(url, title):
            return _title(bot, channel, title, redundant=True)   
        else:
            return _title(bot, channel, title)
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
    log.info(title)

    if not info:
        return bot.say(channel, "%s '%s'%s" % (prefix, title, suffix))
    else:
        return bot.say(channel, "%s '%s' [%s]" % (prefix, title, info))

##### HANDLERS #####

def _handle_hs(url):
    """*hs.fi*artikkeli*"""
    bs = getUrl(url).getBS()
    if not bs: return
    title = bs.title.string
    title = title.split("-")[0].strip()

    try:
        # determine article age and warn if it is too old
        from datetime import datetime
        # handle updated news items of format, and get the latest update stamp
        # 20.7.2010 8:02 | Päivitetty: 20.7.2010 12:53
        date = bs.first('p', {'class':'date'}).next
        # in case hs.fi changes the date format, don't crash on it
        if date:
            date = date.split("|")[0].strip()
            article_date = datetime.strptime(date, "%d.%m.%Y %H:%M")
            delta = datetime.now() - article_date

            if delta.days > 365:
                return title, "NOTE: Article is %d days old!" % delta.days
            else:
                return title
        else:
            return title
    except Exception, e:
        log.error("Error when parsing hs.fi: %s" % e)
        return title

def _handle_ksml(url):
    """*ksml.fi/uutiset*"""
    bs = getUrl(url).getBS()
    if not bs: return
    title = bs.title.string
    title = title.split("-")[0].strip()
    return title

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

    return title

def _handle_iltasanomat(url):
    """*iltasanomat.fi*uutinen.asp*"""
    bs = getUrl(url).getBS()
    if not bs: return

    title = bs.title.string.rsplit(" - ", 1)[0]

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
    price = str(bs.first(text="Hinta:").next.next.next.next.next.string).split("&")[0]

    return u"%s | %s€" % (product, price)


def _handle_yle(url):
    """http://*yle.fi/uutiset/*"""
    bs = getUrl(url).getBS()
    if not bs: return

    title = bs.title.string
    title = title.split("|")[0].strip()

    return title

def _handle_mol(url):
    """http://www.mol.fi/paikat/Job.do?*"""
    bs = getUrl(url).getBS()
    if not bs: return

    title = bs.first("div", {'class':'otsikko'}).string

    return title

def _handle_helmet(url):
    """http://www.helmet.fi/record=*"""
    bs = getUrl(url).getBS()
    if not bs: return

    title = bs.first("strong").string

    return title

def _handle_tweet(url):
    """http*://twitter.com/*/status/*"""
    bs = getUrl(url).getBS()
    if not bs: return

    status = bs.first("span", {'class':'entry-content'}).findAll(text=True)
    content = ""
    for i in status:
        content += i

    published = bs.first("span", {'class':'published timestamp'})['data']
    import time
    # Fri Feb 05 17:40:13 +0000 2010
    published = time.strptime(published[7:37], "%a %b %d %H:%M:%S +0000 %Y")
    published = time.strftime("%Y-%m-%d %H:%M", published)

    title = "(%s) %s" % (published, content)

    return title

def _handle_netanttila(url):
    """http://www.netanttila.com/webapp/wcs/stores/servlet/ProductDisplay*"""
    bs = getUrl(url).getBS()
    
    itemname = bs.first("h1").string.replace("\n", "").replace("\r", "").replace("\t", "").strip()
    price = bs.first("td", {'class': 'right highlight'}).string.split(" ")[0]

    return "%s | %s EUR" % (itemname, price)

def _handle_varttifi(url):
    """http://www.vartti.fi/artikkeli/*"""
    bs = getUrl(url).getBS()

    title = bs.first("h2").string

    return title

def _handle_youtube_shorturl(url):
    """http://youtu.be/*"""
    return _handle_youtube_gdata(url)

def _handle_youtube_gdata_new(url):
    """http://youtube.com/watch#!v=*"""
    return _handle_youtube_gdata(url)

def _handle_youtube_gdata(url):
    """http://*youtube.com/watch?*v=*"""
    gdata_url = "http://gdata.youtube.com/feeds/api/videos/%s"

    match = re.match("http://youtu.be/(.*)", url)
    if not match:
        match = re.match("http://.*?youtube.com/watch\?.*?v=([^&]+)", url)
    if match:
        infourl = gdata_url % match.group(1)
        bs = getUrl(infourl).getBS()
    
        entry = bs.first("entry")

        if not entry: 
            log.info("Video too recent, no info through API yet.")
            return

        author = entry.author.next.string
        # if an entry doesn't have a rating, the whole element is missing
        try:
            rating = float(entry.first("gd:rating")['average'])
        except TypeError:
            rating = 0.0

        stars = int(round(rating)) * "*"
            
        statistics = entry.first("yt:statistics")
        if statistics:
            views = statistics['viewcount']
        else:
            views = "no"

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

def _handle_helmet(url):
    """http://www.helmet.fi/record=*fin"""
    bs = getUrl(url).getBS()
    if not bs: return
 
    title = bs.find(attr={'class':'bibInfoLabel'},text='Teoksen nimi').next.next.next.next.string
 
    return title
 
def _handle_ircquotes(url):
    """http://*ircquotes.fi/[?]*"""
    bs = getUrl(url).getBS()
    if not bs: return
 
    chan = bs.first("span", {'class':'quotetitle'}).next.next.string
    points = bs.first("span", {'class':'points'}).next.string
    firstline = bs.first("div", {'class':'quote'}).next.string
 
    title = "%s (%s): %s" % (chan, points, firstline)
 
    return title


def _handle_alko2(url):
    """http://alko.fi/tuotteet/fi/*"""
    return _handle_alko(url)
    
def _handle_alko(url):
    """http://www.alko.fi/tuotteet/fi/*"""

    bs = getUrl(url).getBS()
    if not bs: return

    name = bs.find('span', {'class':'tuote_otsikko'}).string
    price = bs.find('span', {'class':'tuote_hinta'}).string.split(" ")[0]+u"€"
    drinktype = bs.find('span', {'class':'tuote_tyyppi'}).next

    return name+" - "+drinktype+" - "+price

def _handle_salakuunneltua(url):
    """*salakuunneltua.fi*"""
    return None


def _handle_facebook(url):
    """*facebook.com/*"""
    if re.match("http(s?)://(www\.?)facebook\.com/event\\.php\\?eid=(\\d+)", url):
      url = "https://graph.facebook.com/%s" % url.split('eid=')[1]
      data = json.loads(getUrl(url).getContent())
      title = data['name']
    elif re.match("http(s?)://(www\.?)facebook\.com/profile\\.php\\?id=(\\d+)", url):
      url = "https://graph.facebook.com/%s" % url.split('id=')[1]
      data = json.loads(getUrl(url).getContent())
      title = data['name']
    elif re.match("http(s?)://(www\.?)facebook\.com/group\\.php\\?gid=(\\d+)", url):
      url = "https://graph.facebook.com/%s" % url.split('gid=')[1]
      data = json.loads(getUrl(url).getContent())
      title = data['name']
    elif re.match("http(s?)://(www\.?)facebook\.com/(.*?)", url):
      url = "https://graph.facebook.com/%s" % url.split('/')[-1]
      data = json.loads(getUrl(url).getContent())
      title = data['name']
    else:
      return    

    return title

def _handle_vimeo(url):
    """*vimeo.com/*"""

    data_url = "http://vimeo.com/api/v2/video/%s.xml"

    match = re.match("http://.*?vimeo.com/(\d+)", url)
    if match:
        infourl = data_url % match.group(1)
        bs = getUrl(infourl).getBS()
    
        title = bs.first("title").string
        user = bs.first("user_name").string
        likes = bs.first("stats_number_of_likes").string
        plays = bs.first("stats_number_of_plays").string

        return "%s by %s [%s likes, %s views]" % (title, user, likes, plays)
