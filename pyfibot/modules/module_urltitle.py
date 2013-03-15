# -*- coding: utf-8 -*-
"""Displays HTML page titles

Smart title functionality for sites which could have clear titles,
but still decide show idiotic bulk data in the HTML title element
"""

from __future__ import print_function, division
import fnmatch
import urlparse
import logging
import re

has_json = True
# import py2.6+ json if available, fall back to simplejson
try:
    import json
except:
    try:
        import simplejson as json
    except ImportError, error:
        print('Error starting rss module: %s' % error)
        has_json = False

from types import TupleType

from repoze.lru import ExpiringLRUCache

from bs4 import BeautifulSoup

log = logging.getLogger("urltitle")
config = None
bot = None

# Caching for url titles
cache_timeout = 300  # 300 second timeout for cache
cache = ExpiringLRUCache(10, cache_timeout)


def init(botref):
    global config
    global bot
    bot = botref
    config = bot.config.get("module_urltitle", {})


def __get_bs(url):
    r = bot.get_url(url)
    if not r:
        return None

    content_type = r.headers['content-type'].split(';')[0]
    if content_type not in ['text/html', 'text/xml', 'application/xhtml+xml']:
        log.debug("Content-type %s not parseable" % content_type)
        return None

    content = r.content
    if content:
        return BeautifulSoup(content)
    else:
        return None


def handle_url(bot, user, channel, url, msg):
    """Handle urls"""

    if msg.startswith("-"):
        return
    if re.match("http://.*?\.imdb\.com/title/tt([0-9]+)/?", url):
        return  # IMDB urls are handled elsewhere
    if re.match("(http:\/\/open.spotify.com\/|spotify:)(album|artist|track)([:\/])([a-zA-Z0-9]+)\/?", url):
        return  # spotify handled elsewhere

    if channel.lstrip("#") in config.get('disable', ''):
        return

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

    # Check if the url already has a title cached
    # title = cache.get(url)
    # if title:
    #     log.debug("Cache hit")
    #     return _title(bot, channel, title, True)

    # try to find a specific handler for the URL
    handlers = [(h, ref) for h, ref in globals().items() if h.startswith("_handle_")]

    for handler, ref in handlers:
        pattern = ref.__doc__.split()[0]
        if fnmatch.fnmatch(url, pattern):
            title = ref(url)
            if title:
                cache.put(url, title)
                # handler found, abort
                return _title(bot, channel, title, True)

    log.debug("No specific handler found, using generic")
    # Fall back to generic handler
    bs = __get_bs(url)
    if not bs:
        log.debug("No BS available, returning")
        return

    title = bs.find('title')
    # no title attribute
    if not title:
        log.debug("No title found, returning")
        return

    try:
        # remove trailing spaces, newlines, linefeeds and tabs
        title = title.string.strip()
        title = title.replace("\n", " ")
        title = title.replace("\r", " ")
        title = title.replace("\t", " ")

        # compress multiple spaces into one
        title = re.sub("[ ]{2,}", " ", title)

        # nothing left in title (only spaces, newlines and linefeeds)
        if not title:
            return

        # Cache generic titles
        cache.put(url, title)

        if config.get("check_redundant", True) and _check_redundant(url, title):
            log.debug("%s is redundant, not displaying" % title)
            return

        ignored_titles = ['404 Not Found', '403 Forbidden']
        if title in ignored_titles:
            return
        else:
            return _title(bot, channel, title)

    except AttributeError:
        # TODO: Nees a better way to handle this. Happens with empty <title> tags
        pass


def _check_redundant(url, title):
    """Returns true if the url and title are similar enough."""
    # Remove hostname from the title
    hostname = urlparse.urlparse(url.lower()).netloc
    hostname = ".".join(hostname.split('@')[-1].split(':')[0].lstrip('www.').split('.'))
    cmp_title = title.lower()
    for part in hostname.split('.'):
        idx = cmp_title.replace(' ', '').find(part)
        if idx != -1:
            break

    if idx > len(cmp_title) / 2:
        cmp_title = cmp_title[0:idx + (len(title[0:idx]) - len(title[0:idx].replace(' ', '')))].strip()
    elif idx == 0:
        cmp_title = cmp_title[idx + len(hostname):].strip()
    # Truncate some nordic letters
    unicode_to_ascii = {u'\u00E4': 'a', u'\u00C4': 'A', u'\u00F6': 'o', u'\u00D6': 'O', u'\u00C5': 'A', u'\u00E5': 'a'}
    for i in unicode_to_ascii:
        cmp_title = cmp_title.replace(i, unicode_to_ascii[i])

    cmp_url = url.replace("-", " ")
    cmp_url = url.replace("+", " ")
    cmp_url = url.replace("_", " ")

    parts = cmp_url.lower().rsplit("/")

    distances = []
    for part in parts:
        if part.rfind('.') != -1:
            part = part[:part.rfind('.')]
        distances.append(_levenshtein_distance(part, cmp_title))

    if len(title) < 20 and min(distances) < 5:
        return True
    elif len(title) >= 20 and len(title) <= 30 and min(distances) < 10:
        return True
    elif len(title) > 30 and len(title) <= 60 and min(distances) <= 21:
        return True
    elif len(title) > 60 and min(distances) < 37:
        return True
    return False


def _levenshtein_distance(s, t):
    d = [[i] + [0] * len(t) for i in xrange(0, len(s) + 1)]
    d[0] = [i for i in xrange(0, (len(t) + 1))]

    for i in xrange(1, len(d)):
        for j in xrange(1, len(d[i])):
            if len(s) > i - 1 and len(t) > j - 1 and s[i - 1] == t[j - 1]:
                d[i][j] = d[i - 1][j - 1]
            else:
                d[i][j] = min((d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + 1))

    return d[len(s)][len(t)]


def _title(bot, channel, title, smart=False, prefix=None):
    """Say title to channel"""

    if not title:
        return

    if not prefix:
        prefix = "Title:"
    info = None
    # tuple, additional info
    if type(title) == TupleType:
        info = title[1]
        title = title[0]
    # crop obscenely long titles
    if len(title) > 200:
        title = title[:200] + "..."

    if not info:
        return bot.say(channel, "%s %s" % (prefix, title))
    else:
        return bot.say(channel, "%s %s [%s]" % (prefix, title, info))


# TODO: Some handlers does not have if not bs: return, but why do we even have this for every function
def _handle_iltalehti(url):
    """*iltalehti.fi*html"""
    # Go as normal
    bs = __get_bs(url)
    if not bs:
        return
    title = bs.find('title').string
    # The first part is the actual story title, lose the rest
    title = title.split("|")[0].strip()
    return title


def _handle_iltasanomat(url):
    """*iltasanomat.fi*uutinen.asp*"""
    bs = __get_bs(url)
    if not bs:
        return
    title = bs.title.string.rsplit(" - ", 1)[0]
    return title


def _handle_keskisuomalainen_sahke(url):
    """*keskisuomalainen.net*sahkeuutiset/*"""
    bs = __get_bs(url)
    if not bs:
        return
    title = bs.find('p', {'class': 'jotsikko'})
    if title:
        title = title.next.strip()
        return title


def _handle_tietokone(url):
    """http://www.tietokone.fi/uutta/uutinen.asp?news_id=*"""
    bs = __get_bs(url)
    sub = bs.find('h5').string
    main = bs.find('h2').string
    return "%s - %s" % (main, sub)


def _handle_itviikko(url):
    """http://www.itviikko.fi/*/*/*/*/*"""
    bs = __get_bs(url)
    if not bs:
        return
    return bs.find("h1", "headline").string


def _handle_verkkokauppa(url):
    """http://www.verkkokauppa.com/*/product/*"""
    bs = __get_bs(url)
    if not bs:
        return
    product = bs.find('h1', id='productName').string
    try:
        price = bs.find('strong', {'class': 'product-price-label'}).next.next.next
        price = price.getText().replace('&nbsp;', '')
    except:
        price = "???€"
    try:
        availability = bs.find('div', {'id': 'productAvailabilityInfo'}).firstText().getText()
    except:
        availability = ""
    return "%s | %s (%s)" % (product, price, availability)


def _handle_mol(url):
    """http://www.mol.fi/paikat/Job.do?*"""
    bs = __get_bs(url)
    if not bs:
        return
    title = bs.find("div", {'class': 'otsikko'}).string
    return title


def _handle_tweet2(url):
    """http*://twitter.com/*/status/*"""
    return _handle_tweet(url)


def _handle_tweet(url):
    """http*://twitter.com/*/statuses/*"""
    tweet_url = "http://api.twitter.com/1/statuses/show/%s.json"
    test = re.match("https?://twitter\.com\/(\w+)/status(es)?/(\d+)", url)
    #    matches for unique tweet id string
    infourl = tweet_url % test.group(3)

    data = get_url(infourl)

    #reads dict
    ##You can modify the fields below or add any fields you want to the returned string
    text = data.json()['text']
    user = data.json()['user']['screen_name']
    name = data.json()['user']['name']
    tweet = "Tweet by %s(@%s): %s" % (name, user, text)
    return tweet


def _handle_netanttila(url):
    """http://www.netanttila.com/webapp/wcs/stores/servlet/ProductDisplay*"""
    bs = __get_bs(url)
    itemname = bs.find("h1").string.replace("\n", "").replace("\r", "").replace("\t", "").strip()
    price = bs.find("td", {'class': 'right highlight'}).string.split(" ")[0]
    return "%s | %s EUR" % (itemname, price)


def _handle_youtube_shorturl(url):
    """http*://youtu.be/*"""
    return _handle_youtube_gdata(url)


def _handle_youtube_gdata_new(url):
    """http*://youtube.com/watch#!v=*"""
    return _handle_youtube_gdata(url)


def _handle_youtube_gdata(url):
    """http*://*youtube.com/watch?*v=*"""
    gdata_url = "http://gdata.youtube.com/feeds/api/videos/%s"

    match = re.match("https?://youtu.be/(.*)", url)
    if not match:
        match = re.match("https?://.*?youtube.com/watch\?.*?v=([^&]+)", url)
    if match:
        infourl = gdata_url % match.group(1)
        params = {'alt': 'json', 'v': '2'}
        r = get_url(infourl, params=params)

        if not r.status_code == 200:
            log.info("Video too recent, no info through API yet.")
            return

        entry = r.json()['entry']

        author = entry['author'][0]['name']['$t']

        try:
            rating = entry.get('gd$rating', None)['average']
        except TypeError:
            rating = 0.0

        stars = int(round(rating)) * "*"

        try:
            views = entry['yt$statistics']['viewCount']
        except:
            views = 'no'

        title = entry['title']['$t']

        # https://developers.google.com/youtube/2.0/reference#youtube_data_api_tag_media:rating
        rating = entry['media$group'].get('media$rating', None)

        secs = int(entry['media$group']['yt$duration']['seconds'])
        lengthstr = []
        hours, minutes, seconds = secs // 3600, secs // 60 % 60, secs % 60
        if hours > 0:
            lengthstr.append("%dh" % hours)
        if minutes > 0:
            lengthstr.append("%dm" % minutes)
        if seconds > 0:
            lengthstr.append("%ds" % seconds)
        if rating:
            adult = " - XXX"
        else:
            adult = ""
        return "%s by %s [%s - %s - %s views%s]" % (title, author, "".join(lengthstr), "[%-5s]" % stars, views, adult)


def _handle_helmet(url):
    """http://www.helmet.fi/record=*fin"""
    bs = __get_bs(url)
    if not bs:
        return
    title = bs.find(attr={'class': 'bibInfoLabel'}, text='Teoksen nimi').next.next.next.next.string
    return title


def _handle_ircquotes(url):
    """http://*ircquotes.fi/[?]*"""
    bs = __get_bs(url)
    if not bs:
        return
    chan = bs.find("span", {'class': 'quotetitle'}).next.next.string
    points = bs.find("span", {'class': 'points'}).next.string
    firstline = bs.find("div", {'class': 'quote'}).next.string
    title = "%s (%s): %s" % (chan, points, firstline)
    return title


def _handle_alko2(url):
    """http://alko.fi/tuotteet/fi/*"""
    return _handle_alko(url)


def _handle_alko(url):
    """http://www.alko.fi/tuotteet/fi/*"""
    bs = __get_bs(url)
    if not bs:
        return
    name = bs.find('span', {'class': 'tuote_otsikko'}).string
    price = bs.find('span', {'class': 'tuote_hinta'}).string.split(" ")[0] + u"€"
    drinktype = bs.find('span', {'class': 'tuote_tyyppi'}).next
    return name + " - " + drinktype + " - " + price


def _handle_salakuunneltua(url):
    """*salakuunneltua.fi*"""
    return None


def _handle_vimeo(url):
    """*vimeo.com/*"""
    data_url = "http://vimeo.com/api/v2/video/%s.json"
    match = re.match("http://.*?vimeo.com/(\d+)", url)
    if match:
        infourl = data_url % match.group(1)
        r = get_url(infourl)
        info = r.json()[0]
        title = info['title']
        user = info['user_name']
        likes = info['stats_number_of_likes']
        plays = info['stats_number_of_plays']

        secs = info['duration']
        lengthstr = []
        hours, minutes, seconds = secs // 3600, secs // 60 % 60, secs % 60
        if hours > 0:
            lengthstr.append("%dh" % hours)
        if minutes > 0:
            lengthstr.append("%dm" % minutes)
        if seconds > 0:
            lengthstr.append("%ds" % seconds)

        return "%s by %s [%s - %s likes, %s views]" % (title, user, "".join(lengthstr), likes, plays)


def _handle_stackoverflow(url):
    """*stackoverflow.com/questions/*"""
    api_url = 'http://api.stackoverflow.com/1.1/questions/%s'
    match = re.match('.*stackoverflow.com/questions/([0-9]+)', url)
    if match is None:
        return
    question_id = match.group(1)
    content = get_url(api_url % question_id)
    if not content:
        log.debug("No content received")
        return
    try:
        data = content.json()
        title = data['questions'][0]['title']
        tags = "/".join(data['questions'][0]['tags'])
        score = data['questions'][0]['score']
        return "%s - %dpts - %s" % (title, score, tags)
    except Exception, e:
        return "Json parsing failed %s" % e


def _handle_hs(url):
    """*hs.fi*artikkeli*"""
    bs = __get_bs(url)
    if not bs:
        return
    title = bs.title.string
    title = title.split("-")[0].strip()
    try:
        # determine article age and warn if it is too old
        from datetime import datetime
        # handle updated news items of format, and get the latest update stamp
        # 20.7.2010 8:02 | PÃ¤ivitetty: 20.7.2010 12:53
        date = bs.find('p', {'class': 'date'}).next
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


def _handle_mtv3(url):
    """*mtv3.fi*"""
    bs = __get_bs(url)
    title = bs.find("h1", "entry-title").text
    return title


def _handle_yle(url):
    """http://*yle.fi/uutiset/*"""
    bs = __get_bs(url)
    if not bs:
        return
    title = bs.title.string
    title = title.split("|")[0].strip()
    return title


def _handle_varttifi(url):
    """http://www.vartti.fi/artikkeli/*"""
    bs = __get_bs(url)
    title = bs.find("h2").string
    return title


def _handle_aamulehti(url):
    """http://www.aamulehti.fi/*"""
    bs = __get_bs(url)
    if not bs:
        return
    title = bs.find("h1").string
    return title


def _handle_apina(url):
    """http://apina.biz/*"""
    return None


def _handle_areena(url):
    """http://areena.yle.fi/*"""
    bs = __get_bs(url)
    title = bs.html.head.title.text.split(' | ')[0]
    return title


def _handle_imgur(url):
    """http://*imgur.com*"""
    client_id = "a7a5d6bc929d48f"
    api = "https://api.imgur.com/3/"
    headers = {"Authorization": "Client-ID %s" % client_id}

    # regexes and matching API endpoints
    endpoints = [("i.imgur.com/(.*)\.(jpg|png|gif)", "gallery"),
                 ("imgur.com/gallery/(.*)", "gallery"),
                 ("imgur.com/a/([^\?]+)", "album"),
                 ("imgur.com/([^\./]+)", "gallery")
        ]

    endpoint = None
    for regex, _endpoint in endpoints:
        match = re.search(regex, url)
        if match:
            resource_id = match.group(1)
            endpoint = _endpoint
            log.debug("using endpoint %s for resource %s" % (endpoint, resource_id))
            break

    if not endpoint:
        log.debug("No matching imgur endpoint found for %s" % url)
        return "No endpoint found"

    r = get_url("%s/%s/%s" % (api, endpoint, resource_id), headers=headers)
    data = r.json()

    log.debug(data)

    if data['status'] == 200:
        title = r.json()['data']['title']
        # append album size to album urls if it's relevant
        if endpoint == "album":
            imgcount = len(data['data']['images'])
            if imgcount > 1:
                title += " [%d images]" % len(data['data']['images'])
    else:
        log.debug("imgur API error: %d %s" % (data['status'], data['data']['error']))
        return None

    return title
