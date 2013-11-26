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
from datetime import datetime
import math

from types import TupleType

from repoze.lru import ExpiringLRUCache

from bs4 import BeautifulSoup

log = logging.getLogger("urltitle")
config = None
bot = None
handlers = []

TITLE_LAG_MAXIMUM = 10

# Caching for url titles
cache_timeout = 300  # 300 second timeout for cache
cache = ExpiringLRUCache(10, cache_timeout)
CACHE_ENABLED = True


def init(botref):
    global config
    global bot
    global handlers
    bot = botref
    config = bot.config.get("module_urltitle", {})
    # load handlers in init, as the data doesn't change between rehashes anyways
    handlers = [(h, ref) for h, ref in globals().items() if h.startswith("_handle_")]


def __get_bs(url):
    # Fetch the content and measure how long it took
    start = datetime.now()
    r = bot.get_url(url)
    end = datetime.now()

    if not r:
        return None

    duration = (end - start).seconds
    if duration > TITLE_LAG_MAXIMUM:
        log.error("Fetching title took %d seconds, not displaying title" % duration)
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


def __get_length_str(secs):
    lengthstr = []
    hours, minutes, seconds = secs // 3600, secs // 60 % 60, secs % 60
    if hours > 0:
        lengthstr.append("%dh" % hours)
    if minutes > 0:
        lengthstr.append("%dm" % minutes)
    if seconds > 0:
        lengthstr.append("%ds" % seconds)
    if not lengthstr:
        lengthstr = ['0s']
    return ''.join(lengthstr)


def __get_age_str(published):
    age = datetime.now() - published
    halfyears, days = age.days // 182, age.days % 365
    agestr = []
    years = halfyears * 0.5
    if years >= 1:
        agestr.append("%gy" % years)
    # don't display days for videos older than 6 months
    if years < 1 and days > 0:
        agestr.append("%dd" % days)
    # complete the age string
    if agestr and days != 0:
        agestr.append(" ago")
    elif years == 0 and days == 0:  # uploaded TODAY, whoa.
        agestr.append("FRESH")
    else:
        agestr.append("ANANASAKÄÄMÄ")  # this should never happen =)
    return "".join(agestr)


def __get_views(views):
    if int(views) == 0:
        return '0'
    millnames = ['', 'k', 'M', 'Billion', 'Trillion']
    millidx = max(0, min(len(millnames) - 1, int(math.floor(math.log10(abs(views)) / 3.0))))
    return '%.0f%s' % (views / 10 ** (3 * millidx), millnames[millidx])


def command_cache(bot, user, channel, args):
    global CACHE_ENABLED
    if isAdmin(user):
        CACHE_ENABLED = not CACHE_ENABLED
        # cache was just disabled, clear it
        if not CACHE_ENABLED:
            cache.clear()
            bot.say(channel, 'Cache cleared')
        msg = 'Cache status: %s' % ('ENABLED' if CACHE_ENABLED else 'DISABLED')
        bot.say(channel, msg)


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
    if CACHE_ENABLED:
        title = cache.get(url)
        if title:
            log.debug("Cache hit")
            return _title(bot, channel, title, True)

    global handlers
    # try to find a specific handler for the URL
    for handler, ref in handlers:
        pattern = ref.__doc__.split()[0]
        if fnmatch.fnmatch(url, pattern):
            title = ref(url)
            if title is False:
                log.debug("Title disabled by handler.")
                return
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

    # Try and get title meant for social media first, it's usually fairly accurate
    title = bs.find('meta', {'property': 'og:title'})
    if not title:
        title = bs.find('title')
        # no title attribute
        if not title:
            log.debug("No title found, returning")
            return
        title = title.text
    else:
        title = title['content']

    try:
        # remove trailing spaces, newlines, linefeeds and tabs
        title = title.strip()
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


def _handle_verkkokauppa(url):
    """http://www.verkkokauppa.com/*/product/*"""
    bs = __get_bs(url)
    if not bs:
        return
    product = bs.find('h1', id='productName').string
    try:
        price = bs.find('h4', {'itemprop': 'price'}).text.strip()
    except:
        price = "???€"
    try:
        availability = bs.find('div', {'id': 'productAvailabilityInfo'}).find('strong').text.strip()
    except:
        availability = ""
    return "%s | %s (%s)" % (product, price, availability)


def _handle_tweet2(url):
    """http*://twitter.com/*/status/*"""
    return _handle_tweet(url)


def _handle_tweet(url):
    """http*://twitter.com/*/statuses/*"""
    tweet_url = "https://api.twitter.com/1.1/statuses/show.json?id=%s&include_entities=false"
    test = re.match("https?://twitter\.com\/(\w+)/status(es)?/(\d+)", url)
    # matches for unique tweet id string
    infourl = tweet_url % test.group(3)

    bearer_token = config.get("twitter_bearer")
    if not bearer_token:
        log.info("Use util/twitter_application_auth.py to request a bearer token for tweet handling")
        return
    headers = {'Authorization': 'Bearer ' + bearer_token}

    data = bot.get_url(infourl, headers=headers)

    tweet = data.json()
    if 'errors' in tweet:
        for error in tweet['errors']:
            log.warning("Error reading tweet (code %s) %s" % (error['code'], error['message']))
        return

    text = tweet['text']
    user = tweet['user']['screen_name']
    name = tweet['user']['name']

    #retweets  = tweet['retweet_count']
    #favorites = tweet['favorite_count']
    #created   = tweet['created_at']
    #created_date = datetime.strptime(created, "%a %b %d %H:%M:%S +0000 %Y")
    #tweet_age = datetime.now()-created_date

    tweet = "@%s (%s): %s" % (user, name, text)
    return tweet


def _handle_youtube_shorturl(url):
    """http*://youtu.be/*"""
    return _handle_youtube_gdata(url)


def _handle_youtube_gdata_new(url):
    """http*://youtube.com/watch#!v=*"""
    return _handle_youtube_gdata(url)


def _handle_youtube_gdata(url):
    """http*://*youtube.com/watch?*v=*"""
    # Fetches everything the api knows about the video
    #gdata_url = "http://gdata.youtube.com/feeds/api/videos/%s"
    # This fetches everything that is needed by the handle, using partial response.
    gdata_url = "https://gdata.youtube.com/feeds/api/videos/%s?fields=title,author,gd:rating,media:group(yt:duration),media:group(media:rating),yt:statistics,published&alt=json&v=2"

    match = re.match("https?://youtu.be/(.*)", url)
    if not match:
        match = re.match("https?://.*?youtube.com/watch\?.*?v=([^&]+)", url)
    if match:
        infourl = gdata_url % match.group(1)
        params = {'alt': 'json', 'v': '2'}
        r = bot.get_url(infourl, params=params)

        if not r.status_code == 200:
            log.info("Video too recent, no info through API yet.")
            return

        entry = r.json()['entry']

        ## Author
        author = entry['author'][0]['name']['$t']

        ## Rating in stars
        try:
            rating = entry.get('gd$rating', None)['average']
        except TypeError:
            rating = 0.0

        stars = "[%-5s]" % (int(round(rating)) * "*")

        ## View count
        try:
            views = int(entry['yt$statistics']['viewCount'])
            views = __get_views(views)
        except KeyError:
            # No views at all, the whole yt$statistics block is missing
            views = 'no'

        ## Title
        title = entry['title']['$t']

        ## Age restricted?
        # https://developers.google.com/youtube/2.0/reference#youtube_data_api_tag_media:rating
        rating = entry['media$group'].get('media$rating', None)

        ## Content length
        secs = int(entry['media$group']['yt$duration']['seconds'])
        lengthstr = __get_length_str(secs)

        if rating:
            adult = " - XXX"
        else:
            adult = ""

        ## Content age
        published = entry['published']['$t']
        published = datetime.strptime(published, "%Y-%m-%dT%H:%M:%S.%fZ")
        agestr = __get_age_str(published)

        return "%s by %s [%s - %s - %s views - %s%s]" % (title, author, lengthstr, stars, views, agestr, adult)


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
    """http*://alko.fi/tuotteet/*"""
    return _handle_alko(url)


def _handle_alko(url):
    """http*://www.alko.fi/tuotteet/*"""
    bs = __get_bs(url)
    if not bs:
        return
    name = bs.find('h1', {'itemprop': 'name'}).text
    price = float(bs.find('span', {'itemprop': 'price'}).text.replace(',', '.'))
    bottle_size = float(bs.find('div', {'class': 'product-details'}).contents[0].strip().replace(',', '.'))
    e_per_l = float(bs.find('div', {'class': 'product-details'}).contents[4].strip().replace(',', '.'))
    drinktype = bs.find('h3', {'itemprop': 'category'}).text
    alcohol_content = bs.find('td', {'class': 'label'}, text='Alkoholi:') \
        .parent.find_all('td')[-1].text.strip().replace(',', '.').replace(' ', '')

    return re.sub("[ ]{2,}", " ", '%s [%.2fe, %.2fl, %.2fe/l, %s, %s]' % (name, price, bottle_size, e_per_l, drinktype, alcohol_content))


def _handle_salakuunneltua(url):
    """*salakuunneltua.fi*"""
    return False


def _handle_vimeo(url):
    """*vimeo.com/*"""
    data_url = "http://vimeo.com/api/v2/video/%s.json"
    match = re.match("http(s?)://.*?vimeo.com/(\d+)", url)
    if not match:
        return None

    # Title: CGoY Sharae Spears  Milk shower by miletoo [3m1s - [*****] - 158k views - 313d ago - XXX]
    infourl = data_url % match.group(2)
    r = bot.get_url(infourl)
    info = r.json()[0]
    title = info['title']
    user = info['user_name']
    likes = __get_views(info.get('stats_number_of_likes', 0))
    views = __get_views(info.get('stats_number_of_plays', 0))

    agestr = __get_age_str(datetime.strptime(info['upload_date'], '%Y-%m-%d %H:%M:%S'))
    lengthstr = __get_length_str(info['duration'])

    return "%s by %s [%s - %s likes - %s views - %s]" % (title, user, lengthstr, likes, views, agestr)


def _handle_stackoverflow(url):
    """*stackoverflow.com/questions/*"""
    api_url = 'http://api.stackoverflow.com/1.1/questions/%s'
    match = re.match('.*stackoverflow.com/questions/([0-9]+)', url)
    if match is None:
        return
    question_id = match.group(1)
    content = bot.get_url(api_url % question_id)
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


def _handle_reddit(url):
    """*reddit.com/r/*/comments/*/*"""
    if url[-1] != "/":
        ending = "/.json"
    else:
        ending = ".json"
    json_url = url + ending
    content = bot.get_url(json_url)
    if not content:
        log.debug("No content received")
        return
    try:
        data = content.json()[0]['data']['children'][0]['data']
        title = data['title']
        ups = data['ups']
        downs = data['downs']
        score = ups - downs
        num_comments = data['num_comments']
        over_18 = data['over_18']
        result = "%s - %dpts (%d ups, %d downs) - %d comments" % (title, score, ups, downs, num_comments)
        if over_18 is True:
            result = result + " (NSFW)"
        return result
    except:
        # parsing error, use default title
        return


def _handle_aamulehti(url):
    """http://www.aamulehti.fi/*"""
    bs = __get_bs(url)
    if not bs:
        return
    title = bs.find("h1").string
    return title


def _handle_apina(url):
    """http://apina.biz/*"""
    return False


def _handle_areena(url):
    """http://areena.yle.fi/*"""
    def areena_get_exit_str(text):
        dt = datetime.strptime(text, '%Y-%m-%dT%H:%M:%S') - datetime.now()
        if dt.days > 7:
            return u'%i weeks' % (dt.days / 7)
        if dt.days >= 1:
            return u'%i days' % (dt.days)
        if dt.seconds >= 3600:
            return u'%i hours' % (dt.seconds / 3600)
        return u'%i minutes' % (dt.seconds / 60)

    splitted = url.split('/')
    # if "suora" found in url (and in the correct place),
    # needs a bit more special handling as no api is available
    if len(splitted) > 4 and splitted[4] == 'suora':
        bs = __get_bs(url)
        try:
            container = bs.find('section', {'class': 'simulcast'})
        except:
            return
        channel = container.find('a', {'class': 'active'}).text.strip()
        return '%s (LIVE)' % (channel)

    # create json_url from original url
    json_url = '%s.json' % url.split('?')[0]
    r = bot.get_url(json_url)

    try:
        data = r.json()
    except:
        log.debug("Couldn't parse JSON.")
        return

    try:
        content_type = data['contentType']
    except KeyError:
        # there's no clear identifier for series
        if 'episodeCountTotal' in data:
            content_type = 'SERIES'
        else:
            # assume EPISODE
            content_type = 'EPISODE'

    try:
        if content_type in ['EPISODE', 'CLIP', 'PROGRAM']:
            # sometimes there's a ": " in front of the name for some reason...
            name = data['reportingTitle'].lstrip(': ')
            duration = __get_length_str(data['durationSec'])
            broadcasted = __get_age_str(datetime.strptime(data['published'], '%Y-%m-%dT%H:%M:%S'))
            if data['expires']:
                expires = ' - exits in %s' % areena_get_exit_str(data['expires'])
            else:
                expires = ''
            play_count = __get_views(data['playCount'])
            return '%s [%s - %s plays - %s%s]' % (name, duration, play_count, broadcasted, expires)

        elif content_type == 'SERIES':
            name = data['name']
            episodes = data['episodeCountViewable']
            latest_episode = __get_age_str(datetime.strptime(data['previousEpisode']['published'], '%Y-%m-%dT%H:%M:%S'))
            return '%s [SERIES - %d episodes - latest episode: %s]' % (name, episodes, latest_episode)
    except:
        # We want to exit cleanly, so it falls back to default url handler
        log.debug('Unhandled error in Areena.')
        return


def _handle_wikipedia(url):
    """*wikipedia.org*"""
    def get_redirect(content):
        if '#redirect' in content.lower() or \
           '<li>redirect' in content.lower():
            return True
        return False

    def clean_page_name(url):
        # select part after '/' as article and unquote it (replace stuff like %20) and decode to unicode
        page = bot.to_unicode(urlparse.unquote(url.split('/')[-1]))
        if page.startswith('index.php') and 'title' in page:
            page = page.split('?title=')[1]
        return page

    def get_content(url):
        params = {
            'format': 'json',
            'action': 'parse',
            'prop': 'text',
            'section': 0,
            'page': clean_page_name(url)
        }

        language = url.split('/')[2].split('.')[0]
        api = "http://%s.wikipedia.org/w/api.php" % (language)

        r = bot.get_url(api, params=params)
        try:
            content = r.json()['parse']['text']['*']
        except KeyError:
            return
        # index to keep track of redirections
        redirection_index = 0
        # loop while we get a redirection
        while get_redirect(content):
            try:
                params['page'] = clean_page_name(BeautifulSoup(content).find('li').find('a').get('href'))
            except:
                return
            r = bot.get_url(api, params=params)
            try:
                content = r.json()['parse']['text']['*']
            except KeyError:
                return
            # increase redirection index and if it seems like we're in endless loop,
            # fall back to default handler
            redirection_index += 1
            if redirection_index > 5:
                return
        content = BeautifulSoup(content)
        # remove tables as un-necessary (don't contain any info we'd want, usually tables on the right)
        [x.extract() for x in content.findAll('table')]
        return content

    def find_first_paragraph(content):
        # find the first paragraph, sometimes the first "<p>" is empty
        for paragraph in content.findAll('p'):
            # if there's an image in the paragraph, it's most likely incorrectly formatted page
            #   -> select next paragraph
            # NOTE: This might not be needed after removing the table, leaving it for now...
            if paragraph.find('img'):
                continue
            # ignore if the paragraph has coordinates in it
            # (most likely it's the coordinates in top right corner then)
            if paragraph.find('span', attrs={'id': 'coordinates'}):
                continue
            first_paragraph = paragraph.text.strip()
            if first_paragraph:
                # Remove all annotations to make splitting easier
                first_paragraph = re.sub(r'\[.*?\]', '', first_paragraph)
                # Cleanup brackets (usually includes useless information to IRC)
                first_paragraph = re.sub(r'\(.*?\)', '', first_paragraph)
                # Remove " , ", which might be left behind after cleaning up the brackets
                first_paragraph = first_paragraph.replace(' , ', ', ')
                # Remove multiple spaces
                first_paragraph = re.sub(' +', ' ', first_paragraph)
                return first_paragraph

    content = get_content(url)
    if not content:
        return

    first_paragraph = find_first_paragraph(content)
    if not first_paragraph:
        return

    # Define sentence break as something ending in a period and starting with a capital letter,
    # with a whitespace or newline in between
    sentences = re.split('\.\s[A-ZÅÄÖ]', first_paragraph)
    # Remove empty values from list.
    sentences = filter(None, sentences)

    if not sentences:
        return

    first_sentence = sentences[0]
    # After regex splitting, the dot shold be removed, add it.
    if first_sentence[-1] != '.':
        first_sentence += '.'

    length_threshold = 450
    if len(first_sentence) <= length_threshold:
        return first_sentence

    # go through the first sentence from threshold to end
    # and find either a space or dot to cut to.
    for i in range(length_threshold, len(first_sentence)):
        char = first_sentence[i]
        if char == ' ' or char == '.':
            # if dot was found, the sentence probably ended, so no need to print "..."
            if char == '.':
                return first_sentence[:i + 1]
            # if we ended up on a space, print "..."
            return first_sentence[:i + 1] + '...'


def _handle_imgur(url):
    """http://*imgur.com*"""

    def create_title(data):
        section = data['data']['section']
        title = data['data']['title']
        if section:
            return "%s (/r/%s)" % (title, section)
        else:
            return title

    client_id = "a7a5d6bc929d48f"
    api = "https://api.imgur.com/3"
    headers = {"Authorization": "Client-ID %s" % client_id}

    # regexes and matching API endpoints
    endpoints = [("imgur.com/r/.*?/(.*)", "gallery/r/all"),
                 ("i.imgur.com/(.*)\.(jpg|png|gif)", "gallery"),
                 ("imgur.com/gallery/(.*)", "gallery"),
                 ("imgur.com/a/([^\?]+)", "album"),
                 ("imgur.com/([^\./]+)", "gallery")]

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

    r = bot.get_url("%s/%s/%s" % (api, endpoint, resource_id), headers=headers)
    if not r.content:
        if endpoint != "gallery/r/all":
            endpoint = "gallery/r/all"
            log.debug("switching to endpoint gallery/r/all because of empty response")
            r = bot.get_url("%s/%s/%s" % (api, endpoint, resource_id), headers=headers)
            if not r.content:
                log.warn("Empty response after retry!")
                return
        else:
            log.warn("Empty response!")
            return

    data = r.json()

    if data['status'] == 200:
        title = create_title(r.json())
        # append album size to album urls if it's relevant
        if endpoint == "album":
            imgcount = len(data['data']['images'])
            if imgcount > 1:
                title += " [%d images]" % len(data['data']['images'])
    elif data['status'] == 404 and endpoint != "gallery/r/all":
        endpoint = "gallery/r/all"
        log.debug("Not found, seeing if it is a subreddit image")
        r = bot.get_url("%s/%s/%s" % (api, endpoint, resource_id), headers=headers)
        data = r.json()
        if data['status'] == 200:
            title = create_title(r.json())
        else:
            return None
    else:
        log.debug("imgur API error: %d %s" % (data['status'], data['data']['error']))
        return None

    return title


def _handle_liveleak(url):
    """http://*liveleak.com/view?i=*"""
    try:
        id = url.split('view?i=')[1]
    except IndexError:
        log.debug('ID not found')
        return

    bs = __get_bs(url)
    if not bs:
        return
    title = bs.find('span', 'section_title').text.strip()
    info = str(bs.find('span', id='item_info_%s' % id))

    added_by = '???'
    tags = 'none'
    date_added = '???'
    views = '???'

    # need to do this kind of crap, as the data isn't contained by a span
    try:
        added_by = BeautifulSoup(info.split('<strong>By:</strong>')[1].split('<br')[0]).find('a').text
    except:
        pass

    try:
        date_added = info.split('</span>')[1].split('<span>')[0].strip()
    except:
        pass

    try:
        views = __get_views(int(info.split('<strong>Views:</strong>')[1].split('|')[0].strip()))
    except:
        pass

    try:
        tags = BeautifulSoup(info.split('<strong>Tags:</strong>')[1].split('<br')[0]).text
    except:
        pass

    return '%s by %s [%s views - %s - tags: %s]' % (title, added_by, views, date_added, tags)


def _handle_dailymotion(url):
    """http://*dailymotion.com/video/*"""
    video_id = url.split('/')[-1].split('_')[0]
    params = {
        'fields': ','.join([
            'owner.screenname',
            'title',
            'modified_time',
            'duration',
            'rating',
            'views_total',
            'explicit'
        ]),
        'family_filter': 0,
        'localization': 'en'
    }
    api = 'https://api.dailymotion.com/video/%s'
    try:
        r = bot.get_url(api % video_id, params=params).json()

        lengthstr = __get_length_str(r['duration'])
        stars = "[%-5s]" % (int(round(r['rating'])) * "*")
        views = __get_views(r['views_total'])
        agestr = __get_age_str(datetime.fromtimestamp(r['modified_time']))
        if r['explicit']:
            adult = ' - XXX'
        else:
            adult = ''

        return "%s by %s [%s - %s - %s views - %s%s]" % (r['title'], r['owner.screenname'], lengthstr, stars, views, agestr, adult)
    except:
        return


def _handle_ebay(url):
    """http*://*.ebay.*/itm/*"""
    try:
        item_id = url.split('/')[-1].split('?')[0]
    except IndexError:
        log.debug("Couldn't find item ID.")
        return

    app_id = config.get('ebay_appid', 'RikuLind-3b6d-4c30-937c-6e7d87b5d8be')
    # 77 == Germany, prices in EUR
    site_id = config.get('ebay_siteid', 77)
    currency = config.get('ebay_currency', 'e')

    api_url = 'http://open.api.ebay.com/shopping'
    params = {
        'callname': 'GetSingleItem',
        'responseencoding': 'JSON',
        'appid': app_id,
        'siteid': site_id,
        'version': 515,
        'ItemID': item_id,
        'IncludeSelector': 'ShippingCosts'
    }

    r = bot.get_url(api_url, params=params)
    # if status_code != 200 or Ack != 'Success', something went wrong and data couldn't be found.
    if r.status_code != 200 or r.json()['Ack'] != 'Success':
        log.debug("eBay: data couldn't be fetched.")
        return

    item = r.json()['Item']

    name = item['Title']
    # ConvertedCurrentPrice holds the value of item in currency determined by site id
    price = item['ConvertedCurrentPrice']['Value']
    location = '%s, %s' % (item['Location'], item['Country'])

    ended = ''
    if item['ListingStatus'] != 'Active':
        ended = ' - ENDED'

    if 'ShippingCostSummary' in item and \
       'ShippingServiceCost' in item['ShippingCostSummary'] and \
       item['ShippingCostSummary']['ShippingServiceCost']['Value'] != 0:
            price = '%.1f%s (postage %.1f%s)' % (
                price, currency,
                item['ShippingCostSummary']['ShippingServiceCost']['Value'], currency)
    else:
        price = '%.1f%s' % (price, currency)

    try:
        if item['QuantityAvailableHint'] == 'MoreThan':
            availability = 'over %i available' % item['QuantityThreshold']
        else:
            availability = '%d available' % item['QuantityThreshold']
        return '%s [%s - %s - ships from %s%s]' % (name, price, availability, location, ended)
    except KeyError:
        log.debug('eBay: quantity available not be found.')
        return '%s [%s - ships from %s%s]' % (name, price, location, ended)


def _handle_ebay_no_prefix(url):
    """http*://ebay.*/itm/*"""
    return _handle_ebay(url)


def _handle_ebay_cgi(url):
    """http*://cgi.ebay.*/ws/eBayISAPI.dll?ViewItem&item=*"""
    item_id = url.split('item=')[1].split('&')[0]
    fake_url = 'http://ebay.com/itm/%s' % item_id
    return _handle_ebay(fake_url)


def _handle_dealextreme(url):
    """http*://dx.com/p/*"""
    sku = url.split('?')[0].split('-')[-1]
    cookies = {'DXGlobalization': 'lang=en&locale=en-US&currency=EUR'}
    api_url = 'http://dx.com/bi/GetSKUInfo?sku=%s' % sku

    r = bot.get_url(api_url, cookies=cookies)

    try:
        data = r.json()
    except:
        log.debug('DX.com API error.')
        return

    if 'success' not in data or data['success'] is not True:
        log.debug('DX.com unsuccessful')
        return

    if 'products' not in data or len(data['products']) < 1:
        log.debug("DX.com couldn't find products")
        return

    product = data['products'][0]
    name = product['headLine']
    price = float(product['price'].replace(u'€', ''))

    if product['reviewCount'] > 0:
        reviews = product['reviewCount']
        stars = "[%-5s]" % (product['avgRating'] * "*")
        return '%s [%.2fe - %s - %i reviews]' % (name, price, stars, reviews)
    return '%s [%.2fe]' % (name, price)


def _handle_dealextreme_www(url):
    """http*://www.dx.com/p/*"""
    return _handle_dealextreme(url)


def _handle_instagram(url):
    """http*://instagram.com/p/*"""
    from instagram.client import InstagramAPI

    CLIENT_ID = '879b81dc0ff74f179f5148ca5752e8ce'

    api = InstagramAPI(client_id=CLIENT_ID)

    # todo: instagr.am
    m = re.search('instagram\.com/p/([^/]+)/', url)
    if not m:
        return

    shortcode = m.group(1)

    r = bot.get_url("http://api.instagram.com/oembed?url=http://instagram.com/p/%s/" % shortcode)

    media = api.media(r.json()['media_id'])

    # media type video/image?
    # age/date? -> media.created_time  # (datetime object)

    # full name = username for some users, don't bother displaying both
    if media.user.full_name.lower() != media.user.username.lower():
        user = "%s (%s)" % (media.user.full_name, media.user.username)
    else:
        user = media.user.full_name

    return "%s: %s [%d likes, %d comments]" % (user, media.caption.text, media.like_count, media.comment_count)


def _handle_github(url):
    """http*://*github.com*"""
    return False
