# -*- coding: utf-8 -*-
# pylint: disable=unused-variable

"""Displays HTML page titles

Smart title functionality for sites which could have clear titles,
but still decide show idiotic bulk data in the HTML title element
"""

from __future__ import unicode_literals, print_function, division
import fnmatch
import urlparse
import logging
import re
import math
from datetime import datetime, timedelta
from types import TupleType
from dateutil.tz import tzutc
from dateutil.parser import parse as parse_datetime

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
    """Initialize the urltitle module"""

    global config
    global bot
    global handlers
    bot = botref
    config = bot.config.get("module_urltitle", {})
    # load handlers in init, as the data doesn't change between rehashes anyways
    handlers = [(h, ref) for h, ref in globals().items() if h.startswith("_handle_")]


def __get_bs(url):
    """Attempt to get a beautifulsoup object for the given url"""

    # Fetch the content and measure how long it took
    start = datetime.now()
    r = bot.get_url(url)
    end = datetime.now()

    if not r:
        return None

    duration = (end - start).seconds
    if duration > TITLE_LAG_MAXIMUM:
        log.error("Fetching title took %d seconds, not displaying title", duration)
        return None

    content_type = r.headers['content-type'].split(';')[0]
    if content_type not in ['text/html', 'text/xml', 'application/xhtml+xml']:
        log.debug("Content-type %s not parseable", content_type)
        return None

    if r.content:
        return BeautifulSoup(r.content, 'html.parser')
    else:
        return None


def __get_title_tag(url):
    """Get the plain title tag for the site"""

    bs = __get_bs(url)
    if not bs:
        return False

    title = bs.find('title')
    if not title:
        return

    return title.text


def __get_length_str(secs):
    """Convert seconds to human readable string"""

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


def __get_age_str(published, use_fresh=True):
    """Convert delta time to human readable format"""

    now = datetime.now(tz=published.tzinfo)

    # Check if the publish date is in the future (upcoming episode)
    if published > now:
        age = published - now
        future = True
    else:
        age = now - published
        future = False

    secs = age.total_seconds()

    halfyears, days, hours, minutes = age.days // 182, age.days % 365, secs // 3600, secs // 60 % 60

    agestr = []
    years = halfyears * 0.5

    # uploaded TODAY, whoa.
    if years == 0 and days == 0 and use_fresh:
        return 'FRESH'

    if years >= 1:
        agestr.append("%gy" % years)
    # don't display days for videos older than 6 months
    if years < 1 and days > 0:
        agestr.append("%dd" % days)

    if not agestr:
        agestr.append('%dh' % hours)

    if not agestr:
        agestr.append('%dm' % minutes)

    if agestr:
        agestr.append(" from now" if future else " ago")

    return "".join(agestr)


def __get_views(views):
    """Convert viewcount to human readable format"""

    if int(views) == 0:
        return '0'
    millnames = ['', 'k', 'M', 'Billion', 'Trillion']
    millidx = max(0, min(len(millnames) - 1,
                         int(math.floor(math.log10(abs(views)) / 3.0))))
    return '%.0f%s' % (views / 10 ** (3 * millidx), millnames[millidx])


# https://developers.google.com/webmasters/ajax-crawling/docs/specification
def __escaped_fragment(url, meta=False):
    url = urlparse.urlsplit(url)
    if not url.fragment or not url.fragment.startswith('!'):
        if not meta:
            return url.geturl()

    query = url.query
    if query:
        query += '&'
    query += '_escaped_fragment_='
    if url.fragment:
        query += url.fragment[1:]

    return urlparse.urlunsplit((url.scheme, url.netloc, url.path, query, ''))


def command_cache(bot, user, channel, args):
    """Enable or disable url title caching"""
    global CACHE_ENABLED
    if bot.isAdmin(user):
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
    if re.match(r"(https?:\/\/open.spotify.com\/|spotify:)(album|artist|track)([:\/])([a-zA-Z0-9]+)\/?", url):
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

    # Parse shebang fragments according to Google's specification
    if url.rfind('#!') != -1:
        url = __escaped_fragment(url)

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
            elif title is None:
                # Handler found, but suggests using the default title instead
                break
            elif title:
                # handler found, abort
                return _title(bot, channel, title, True, url=url)
            else:
                # No specific handler, use generic
                pass

    # post data to Lambda if enabled
    if config.get('lambda_enable', False):
        lambdafunc = config.get('lambda_url')
        headers = {'x-api-key': config.get('lambda_apikey')}
        outdata = {'url': url, 'channel': channel, 'user': user}

        import requests
        r = requests.post(lambdafunc, json=outdata, headers=headers)
        data = r.json()

        title = data.get('title')
        # Print out the raw response if title isn't found
        if not title:
            print(data)

        _title(bot, channel, data.get('title'))

        return

    log.debug("No specific handler found, using generic")
    # Fall back to generic handler
    bs = __get_bs(url)

    # Handle case of failed connection
    if not bs:
        log.debug("No BS available, returning")
        return

    # According to Google's Making AJAX Applications Crawlable specification
    fragment = bs.find('meta', {'name': 'fragment'})
    if fragment and fragment.get('content') == '!':
        log.debug("Fragment meta tag on page, getting non-ajax version")
        url = __escaped_fragment(url, meta=True)
        bs = __get_bs(url)

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

        if config.get("check_redundant", True) and _check_redundant(url, title):
            log.debug("%s is redundant, not displaying" % title)
            return

        ignored_titles = ['404 Not Found', '403 Forbidden']
        if title in ignored_titles:
            return

        # Return title
        return _title(bot, channel, title, url=url)

    except AttributeError:
        # TODO: Nees a better way to handle this. Happens with empty <title> tags
        pass


def _check_redundant(url, title):
    """Returns true if the url and title are similar enough."""
    # Remove hostname from the title
    hostname = urlparse.urlparse(url.lower()).netloc
    hostname = ".".join(hostname.split(
        '@')[-1].split(':')[0].lstrip('www.').split('.'))
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
    unicode_to_ascii = {u'\u00E4': 'a', u'\u00C4': 'A',
                        u'\u00F6': 'o', u'\u00D6': 'O', u'\u00C5': 'A', u'\u00E5': 'a'}
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
                d[i][j] = min(
                    (d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + 1))

    return d[len(s)][len(t)]


def _title(bot, channel, title, smart=False, prefix=None, url=None):
    """Say title to channel"""

    if not title:
        return

    if url is not None:
        # Cache title
        cache.put(url, title)

    if not prefix:
        prefix = "Title:"
    info = None
    # tuple, additional info
    if type(title) == TupleType:
        info = title[1]
        title = title[0]
    # crop obscenely long titles
    if len(title) > 400:
        title = title[:400] + "..."

    if not info:
        return bot.say(channel, "%s %s" % (prefix, title))
    else:
        return bot.say(channel, "%s %s [%s]" % (prefix, title, info))


def _parse_tweet_from_src(url):
    bs = __get_bs(url)
    if not bs:
        return
    container = bs.find('div', {'class': 'tweet'})
    # Return if tweet container wasn't found.
    if not container:
        return

    name = container.find('strong', {'class': 'fullname'})
    user = container.find('span', {'class': 'username'})
    tweet = container.find('p', {'class': 'tweet-text'})
    # Return string only if every field was found...
    if name and user and tweet:
        return '%s (%s): %s' % (user.text, name.text, tweet.text)


def _handle_mobile_tweet(url):
    """http*://mobile.twitter.com/*/status/*"""
    return _handle_tweet(url)


def _handle_tweet2(url):
    """http*://twitter.com/*/status/*"""
    return _handle_tweet(url)


def _handle_tweet(url):
    """http*://twitter.com/*/statuses/*"""
    tweet_url = "https://api.twitter.com/1.1/statuses/show.json?id=%s&include_entities=false&tweet_mode=extended"
    test = re.match(r"https?://.*?twitter\.com\/(\w+)/status(es)?/(\d+)", url)
    if not test:
        return
    # matches for unique tweet id string
    infourl = tweet_url % test.group(3)

    bearer_token = config.get("twitter_bearer")
    if not bearer_token:
        log.info(
            "Use util/twitter_application_auth.py to request a bearer token for tweet handling")
        return _parse_tweet_from_src(url)
    headers = {'Authorization': 'Bearer ' + bearer_token}

    data = bot.get_url(infourl, headers=headers)

    if not data:
        log.warning("Empty response from Twitter api")
        return

    tweet = data.json()
    if 'errors' in tweet:
        for error in tweet['errors']:
            log.warning("Error reading tweet (code %s) %s" %
                        (error['code'], error['message']))
        return

    text = tweet['full_text'].strip()
    user = tweet['user']['screen_name']
    name = tweet['user']['name'].strip()
    verified = tweet['user']['verified']

    retweets = tweet['retweet_count']
    favorites = tweet['favorite_count']
    created_date = parse_datetime(tweet['created_at'])

    def twit_timestr(dt):
        """A coarse timestr function"""

        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        diff = datetime.now(tzutc()) - dt
        if diff.days > 30 * 6:
            return "%i %s %i" % (dt.day, months[dt.month - 1], dt.year)
        elif diff.days > 30:
            return "%i %s" % (dt.day, months[dt.month - 1])
        elif diff.days:
            return "%id" % diff.days
        elif diff.seconds > 3600:
            return "%ih" % (diff.seconds / 3600)
        elif diff.seconds > 60:
            return "%im" % (diff.seconds / 60)
        else:
            return "now"

    user = "@{0}".format(user)
    if verified:
        user = "✔{0}".format(user)

    tweet = "{0} ({1}) {2}: {3} [♻ {4} ♥ {5}]".format(
        name, user, twit_timestr(created_date), text, retweets, favorites)
    return tweet


def _handle_youtube_shorturl(url):
    """http*://youtu.be/*"""
    return _handle_youtube_gdata(url)


def _handle_youtube_gdata_new(url):
    """http*://youtube.com/watch#!v=*"""
    return _handle_youtube_gdata(url)


def _handle_youtube_gdata(url):
    """http*://*youtube.com/watch?*v=*"""

    api_key = config.get('google_apikey',
                         'AIzaSyD5a4Johhq5K0ARWX-rQMwsNz0vTtQbKNY')

    api_url = 'https://www.googleapis.com/youtube/v3/videos'

    # match both plain and direct time url
    match = re.match(r"https?://youtu.be/([^\?]+)([\?#]t=.*)?", url)
    if not match:
        match = re.match(r"https?://.*?youtube.com/watch\?.*?v=([^&#]+)", url)
    if match:
        params = {'id': match.group(1),
                  'part': 'snippet,contentDetails,statistics',
                  'fields': 'items(id,snippet,contentDetails,statistics)',
                  'key': api_key}

        r = bot.get_url(api_url, params=params)

        # get_url returns None on exception
        if r is None:
            return False

        if not r.status_code == 200:
            error = r.json().get('error')
            if error:
                error = '%s: %s' % (error['code'], error['message'])
            else:
                error = r.status_code

            log.warning('YouTube API error: %s', error)
            return

        items = r.json()['items']
        if len(items) == 0:
            return

        entry = items[0]

        channel = entry['snippet']['channelTitle']

        try:
            views = int(entry['statistics']['viewCount'])
            views = __get_views(views)
        except KeyError:
            views = 'no'

        title = entry['snippet']['title']

        rating = entry['contentDetails'].get('contentRating', None)
        if rating:
            rating = rating.get('ytRating', None)

        # The tag value is an ISO 8601 duration in the format PT#M#S
        duration = entry['contentDetails']['duration'][2:].lower()

        if rating and rating == 'ytAgeRestricted':
            agerestricted = " - age restricted"
        else:
            agerestricted = ""

        # Content age
        published = entry['snippet']['publishedAt']
        published = datetime.strptime(published, "%Y-%m-%dT%H:%M:%S.%fZ")
        agestr = __get_age_str(published)

        return "%s by %s [%s - %s views - %s%s]" % (
            title, channel, duration, views, agestr, agerestricted)


def _handle_helmet(url):
    """https://www.helmet.fi/record=*fin"""
    bs = __get_bs(url)
    if not bs:
        return
    title = bs.find(attr={'class': 'bibInfoLabel'},
                    text='Teoksen nimi').next.next.next.next.string
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
    price = float(
        bs.find('span', {'itemprop': 'price'}).text.replace(',', '.'))
    size = float(bs.find(
        'div', {'class': 'product-details'}).contents[0].strip().replace(',', '.'))
    e_per_l = float(bs.find(
        'div', {'class': 'product-details'}).contents[4].strip().replace(',', '.'))
    drinktype = bs.find('h3', {'itemprop': 'category'}).text
    alcohol = float(
        re.sub(
            r'[^\d.]+',
            '',
            bs.find('td', {'class': 'label'}, text='Alkoholi:')
            .parent.find_all('td')[-1].text.replace(',', '.')))
    # value = price / (size * 1000 * alcohol * 0.01 * 0.789 / 12)
    value = price / (size * alcohol * 0.6575)

    return re.sub("[ ]{2,}", " ", '%s [%.2fe, %.2fl, %.1f%%, %.2fe/l, %.2fe/annos, %s]' % (name, price, size, alcohol, e_per_l, value, drinktype))


def _handle_vimeo(url):
    """*vimeo.com/*"""
    data_url = "https://vimeo.com/api/v2/video/%s.json"
    match = re.match(r"http(s?)://.*?vimeo.com/(\d+)", url)
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

    agestr = __get_age_str(datetime.strptime(
        info['upload_date'], '%Y-%m-%d %H:%M:%S'))
    lengthstr = __get_length_str(info['duration'])

    return "%s by %s [%s - %s likes - %s views - %s]" % (title, user, lengthstr, likes, views, agestr)


def _handle_stackoverflow(url):
    """*stackoverflow.com/questions/*"""
    api_url = 'https://api.stackexchange.com/2.2/questions/%s'
    match = re.match(r'.*stackoverflow.com/questions/([0-9]+)', url)
    if match is None:
        return
    question_id = match.group(1)
    content = bot.get_url(api_url % question_id, params={
                          'site': 'stackoverflow'})

    try:
        data = content.json()
        item = data['items'][0]

        title = item['title']
        tags = '/'.join(item['tags'])
        score = item['score']
        return "%s - %dpts - %s" % (title, score, tags)
    except Exception, e:
        log.debug("Json parsing failed %s" % e)
        return


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
        # truncate title so that the point and comment data fits
        title = data['title']
        if len(title) > 170:
            title = "{0:.170}…".format(title)

        score = data['score']
        num_comments = data['num_comments']
        over_18 = data['over_18']

        result = "{0} [{1} pts, {2} comments]".format(
            title, score, num_comments)
        if over_18:
            result = "{0} (NSFW)".format(result)
        return result
    except:
        # parsing error, use default title
        return


def _handle_aamulehti(url):
    """https://www.aamulehti.fi/*"""
    bs = __get_bs(url)
    if not bs:
        return
    title = bs.find("h1").string
    return title


def _handle_areena(url):
    """https://areena.yle.fi/*"""
    def _parse_publication_events(data):
        '''
        Parses publication events from the data.
        Returns:
            - ScheduledTransmission
            - OnDemandPublication
            - first broadcast time (or if in the future, the start of availability on-demand) [datetime]
            - the exit time of the on-demand [datetime]
        '''
        now = datetime.utcnow().replace(tzinfo=tzutc())

        # Finds all publicationEvents from the data.
        publicationEvents = data.get('publicationEvent', [])

        # Finds the scheduled transmissions
        ScheduledTransmission = [event for event in publicationEvents if event.get(
            'type') == 'ScheduledTransmission']
        if ScheduledTransmission:
            # If transmissions are found, use the first one
            ScheduledTransmission = ScheduledTransmission[0]

        # Finds the on-demand transmissions
        OnDemandPublication = [event for event in publicationEvents if event.get(
            'temporalStatus') == 'currently' and event.get('type') == 'OnDemandPublication']
        if OnDemandPublication:
            # If transmissions are found, use the first one
            OnDemandPublication = OnDemandPublication[0]

        # Find the broadcast time of the transmission
        # First, try to get the time when the on-demand was added to Areena.
        broadcasted = parse_datetime(
            OnDemandPublication['startTime']) if OnDemandPublication and 'startTime' in OnDemandPublication else None
        if broadcasted is None or broadcasted > now:
            # If on-demand wasn't found, fall back to the scheduled transmission.
            broadcasted = parse_datetime(
                ScheduledTransmission['startTime']) if ScheduledTransmission and 'startTime' in ScheduledTransmission else None

        # Find the exit time of the on-demand publication
        exits = None
        if OnDemandPublication and 'endTime' in OnDemandPublication:
            exits = parse_datetime(OnDemandPublication['endTime'])

        return ScheduledTransmission, OnDemandPublication, broadcasted, exits

    def get_duration(event):
        ''' Parses duration of an event, returns integer value in seconds. '''
        if not event:
            return

        duration = event.get('duration') or event.get(
            'media', {}).get('duration')
        if duration is None:
            return

        match = re.match(
            r'P((\d+)Y)?((\d+)D)?T?((\d+)H)?((\d+)M)?((\d+)S)?', duration)
        if not match:
            return

        # Get match group values, defaulting to 0
        match_groups = match.groups(0)

        # Kind of ugly, but works...
        secs = 0
        secs += int(match_groups[1]) * 365 * 86400
        secs += int(match_groups[3]) * 86400
        secs += int(match_groups[5]) * 3600
        secs += int(match_groups[7]) * 60
        secs += int(match_groups[9])
        return secs

    def get_episode(identifier):
        ''' Gets episode information from Areena '''
        url = 'https://external.api.yle.fi/v1/programs/items/%s.json' % (
            identifier)
        params = {
            'app_id': config.get('areena', {}).get('app_id', 'cd556936'),
            'app_key': config.get('areena', {}).get('app_key', '25a08bbaa8101cca1bf0d1879bb13012'),
        }
        r = bot.get_url(url=url, params=params)
        if r.status_code != 200:
            return

        data = r.json().get('data', None)
        if not data:
            return

        title = data.get('title', {}).get('fi', None)
        if not title:
            return

        episode_number = data.get('episodeNumber', -100)
        season_number = data.get('partOfSeason', {}).get('seasonNumber', -100)

        if episode_number != -100 and season_number != -100:
            title += ' - %dx%02d' % (season_number, episode_number)

        promotionTitle = data.get('promotionTitle', {}).get('fi')
        if promotionTitle:
            title += ' - %s' % promotionTitle

        duration = get_duration(data)

        _, OnDemandPublication, broadcasted, exits = _parse_publication_events(
            data)

        title_data = []
        if duration:
            title_data.append(__get_length_str(duration))
        if broadcasted:
            title_data.append(__get_age_str(broadcasted))
        if exits and datetime.now(tz=tzutc()) + timedelta(days=2 * 365) > exits:
            title_data.append('exits in %s' %
                              __get_age_str(exits, use_fresh=False))
        if not OnDemandPublication:
            title_data.append('not available')
        return '%s [%s]' % (title, ' - '.join(title_data))

    def get_series(identifier):
        ''' Gets series information from Areena '''
        url = 'https://external.api.yle.fi/v1/programs/items.json'
        params = {
            'app_id': config.get('areena', {}).get('app_id', 'cd556936'),
            'app_key': config.get('areena', {}).get('app_key', '25a08bbaa8101cca1bf0d1879bb13012'),
            'series': identifier,
            'order': 'publication.starttime:desc',
            'availability': 'ondemand',
            'type': 'program',
            'limit': 100,
        }
        r = bot.get_url(url=url, params=params)
        if r.status_code != 200:
            return

        data = r.json().get('data', None)
        if not data:
            return

        latest_episode = data[0]
        title = latest_episode.get('title', {}).get('fi', None)
        if not title:
            return

        _, _, broadcasted, _ = _parse_publication_events(latest_episode)

        title_data = ['SERIES']
        if len(data) >= 100:
            title_data.append('100+ episodes')
        else:
            title_data.append('%i episodes' % len(data))
        if broadcasted:
            title_data.append('latest episode: %s' %
                              __get_age_str(broadcasted))

        return '%s [%s]' % (title, ' - '.join(title_data))

    # There's still no endpoint to fetch the currently playing shows via API :(
    if 'suora' in url:
        bs = __get_bs(url)
        if not bs:
            return
        container = bs.find('div', {'class': 'selected'})
        channel = container.find('h3').text
        try:
            program = container.find(
                'li', {'class': 'current-broadcast'}).find('div', {'class': 'program-title'})
        except AttributeError:
            return '%s (LIVE)' % (channel)

        link = program.find('a').get('href', None)
        if not link:
            return '%s - %s (LIVE)' % (channel, program.text.strip())
        return '%s - %s <https://areena.yle.fi/%s> (LIVE)' % (channel, program.text.strip(), link.lstrip('/'))

    try:
        identifier = url.split('/')[-1].split('?')[0]
    except:
        log.debug('Areena identifier could not be found.')
        return

    # Try to get the episode (preferred) or series information from Areena
    return get_episode(identifier) or get_series(identifier)


def _handle_wikipedia(url):
    """*wikipedia.org*"""

    def clean_page_name(url):
        # select part after '/' as article and unquote it (replace stuff like %20) and decode to unicode
        page = bot.to_unicode(urlparse.unquote(url.split('/')[-1]))
        if page.startswith('index.php') and 'title' in page:
            page = page.split('?title=')[1]
        return page

    def get_content(url):
        params = {
            'format': 'json',
            'action': 'query',
            'prop': 'extracts',
            # request everything before the first section, because requesting
            # only a limited number of sentences breaks randomly
            'exintro': '',
            'redirects': '',
            'titles': clean_page_name(url)
        }

        language = url.split('/')[2].split('.')[0]
        api = "https://%s.wikipedia.org/w/api.php" % (language)

        r = bot.get_url(api, params=params)

        try:
            content = r.json()['query']['pages'].values()[0]['extract']
            content = BeautifulSoup(content, 'html.parser').get_text()
        except KeyError:
            return
        return content

    content = get_content(url)
    if not content:
        return

    # Remove all annotations to make splitting easier
    content = re.sub(r'\[.*?\]', '', content)
    # Cleanup brackets (usually includes useless information to
    # IRC)
    content = re.sub(r'\(.*?\)', '', content)
    # Remove " , ", which might be left behind after cleaning up
    # the brackets
    content = re.sub(r'\s+([,.])', '\\1 ', content)
    # Remove multiple spaces
    content = re.sub(r'\s+', ' ', content)
    # Strip possible trailing whitespace
    content = content.rstrip()

    # Define sentence break as something ending in a period and starting with a capital letter,
    # with a whitespace or newline in between
    sentences = re.split(r'\.\s(?=[A-ZÅÄÖ])', content)
    # Remove empty values from list.
    sentences = filter(None, sentences)

    if not sentences:
        return

    content = sentences[0]
    # For example titles (Dr., etc.) confuse the splitter
    if len(content) <= 20:
        content = '. '.join(sentences[0:2])
    # After regex splitting, the dot shold be removed, add it.
    if not content.endswith('.'):
        content += '.'

    if not content:
        return
    else:
        return content


def _handle_imgur(url):
    """http*://*imgur.com*"""

    def create_title(data):
        section = data['data']['section']
        title = data['data']['title']

        if not title:
            # If title wasn't found, use title and section of first image
            title = data['data']['images'][0]['title']
            section = data['data']['images'][0]['section']

        if section:
            return "%s (/r/%s)" % (title, section)
        return title

    client_id = "a7a5d6bc929d48f"
    api = "https://api.imgur.com/3"
    headers = {"Authorization": "Client-ID %s" % client_id}

    # regexes and matching API endpoints
    endpoints = [(r"imgur.com/r/.*?/(.*)", "gallery/r/all"),
                 (r"i.imgur.com/(.*)\.(jpg|png|gif)", "gallery"),
                 (r"imgur.com/gallery/(.*)", "gallery"),
                 (r"imgur.com/a/([^\?]+)", "album"),
                 (r"imgur.com/([^\./]+)", "gallery")]

    endpoint = None
    for regex, _endpoint in endpoints:
        match = re.search(regex, url)
        if match:
            resource_id = match.group(1)
            endpoint = _endpoint
            log.debug("using endpoint %s for resource %s" %
                      (endpoint, resource_id))
            break

    if not endpoint:
        log.debug("No matching imgur endpoint found for %s" % url)
        return "No endpoint found"

    r = bot.get_url("%s/%s/%s" % (api, endpoint, resource_id), headers=headers)
    if not r.content:
        if endpoint != "gallery/r/all":
            endpoint = "gallery/r/all"
            log.debug(
                "switching to endpoint gallery/r/all because of empty response")
            r = bot.get_url("%s/%s/%s" %
                            (api, endpoint, resource_id), headers=headers)
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
        r = bot.get_url("%s/%s/%s" %
                        (api, endpoint, resource_id), headers=headers)
        data = r.json()
        if data['status'] == 200:
            title = create_title(r.json())
        else:
            return None
    else:
        log.debug("imgur API error: %d %s" %
                  (data['status'], data['data']['error']))
        return None

    return title


def _handle_liveleak(url):
    """https://*liveleak.com/view?i=*"""
    try:
        id = url.split('view?i=')[1]
    except IndexError:
        log.debug('ID not found')
        return

    bs = __get_bs(url)
    if not bs:
        return
    title = bs.find('span', 'section_title').text.strip()
    info = bs.find('span', id='item_info_%s' % id)
    # we need to render as unicode because if unicode_literals
    info = info.renderContents().decode("iso8859-1")

    # need to do this kind of crap, as the data isn't contained by a span
    try:
        added_by = BeautifulSoup(info.split(
            u'<strong>By:</strong>')[1].split('<br')[0], 'html.parser').find('a').text
    except:
        added_by = '???'

    try:
        date_added = info.split('</span>')[1].split('<span>')[0].strip()
    except:
        date_added = '???'

    try:
        views = __get_views(
            int(info.split('<strong>Views:</strong>')[1].split('|')[0].strip()))
    except:
        views = '???'

    try:
        tags = BeautifulSoup(info.split('<strong>Tags:</strong>')
                             [1].split('<br')[0], 'html.parser').text.strip()
    except:
        tags = 'none'

    return '%s by %s [%s views - %s - tags: %s]' % (title, added_by, views, date_added, tags)


def _handle_dailymotion(url):
    """https://*dailymotion.com/video/*"""
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

    api_url = 'https://open.api.ebay.com/shopping'
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
    fake_url = 'https://ebay.com/itm/%s' % item_id
    return _handle_ebay(fake_url)


def _handle_dealextreme(url):
    """http*://dx.com/p/*"""
    sku = url.split('?')[0].split('-')[-1]
    cookies = {'DXGlobalization': 'lang=en&locale=en-US&currency=EUR'}
    api_url = 'https://www.dx.com/bi/GetSKUInfo?sku=%s' % sku

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
    name = product['shortHeadline']
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
    """https://*instagram.com/p/*"""
    from instagram.client import InstagramAPI

    CLIENT_ID = '879b81dc0ff74f179f5148ca5752e8ce'

    api = InstagramAPI(client_id=CLIENT_ID)

    # todo: instagr.am
    m = re.search(r"instagram\.com/p/([^/]+)", url)
    if not m:
        return

    shortcode = m.group(1)

    r = bot.get_url(
        "https://api.instagram.com/oembed?url=https://instagram.com/p/%s/" % shortcode)

    media = api.media(r.json()['media_id'])

    # media type video/image?
    # age/date? -> media.created_time  # (datetime object)

    # full name = username for some users, don't bother displaying both
    if media.user.full_name.lower() != media.user.username.lower():
        user = "%s (%s)" % (media.user.full_name, media.user.username)
    else:
        user = media.user.full_name

    if media.like_count or media.comment_count:
        info = "["
        if media.like_count:
            info += "%d ♥" % media.like_count
        if media.comment_count:
            info += ", %d comments" % media.comment_count
        info += "]"
    else:
        info = ""

    if media.caption:
        if len(media.caption.text) > 145:
            caption = "{0:.145}…".format(media.caption.text)
        else:
            caption = media.caption.text

        return "%s: %s %s" % (user, caption, info)
    else:
        return "%s: %s" % (user, info)


def fetch_nettiX(url, fields_to_fetch):
    '''
    Creates a title for NettiX -services.
    Uses the mobile site, so at the moment of writing fetching data from
    NettiAsunto and NettiMökki isn't possible.

    All handlers must be implemented elsewhere, this only provides a constant
    function to fetch the data (and creates an uniform title).
    '''

    # Strip useless stuff from url
    site = re.split(r'https?\:\/\/(www.)?(m.)?', url)[-1]
    # Fetch BS from mobile site, as it's a lot easier to parse
    bs = __get_bs('https://m.%s' % site)
    if not bs:
        return

    # Find "main name" for the item
    try:
        main = bs.find('div', {'class': 'head_left'}).find('b').text.strip()
    except AttributeError:
        # If not found, probably doesn't work -> fallback to default
        return
    if not main:
        return

    fields = []

    try:
        # Try to find price for the item, if found -> add to fields
        price = bs.find('div', {'class': 'pl10 mt15 lnht22'}).find(
            'span').text.strip()
        if price:
            fields.append(price)
    except AttributeError:
        pass

    # All sites have the same basic structure, find the "data" table
    ad_info = bs.find('div', {'id': 'ad_info_list'})
    if ad_info:
        for f in ad_info.findAll('li'):
            # Get field name
            field = f.find('div', {'class': 'ad_caption'})
            # Field name ends in colon
            field = field.text.strip()[:-1] if field else None
            # If the name was found and it's in fields_to_fetch
            if field and field in fields_to_fetch:
                # Remove spans
                # For example cars might have registeration date includet in a span
                [s.extract() for s in f.findAll('span')]
                # Get field data
                field_info = f.find(
                    'div', {'class': 'ad_details'}).text.strip()
                # If the data was found and it's not "Ei ilmoitettu", add to fields
                if field_info and field_info != 'Ei ilmoitettu':
                    fields.append(field_info)

    if fields:
        return '%s [%s]' % (main, ', '.join(fields))
    return '%s' % (main)


def _handle_nettiauto(url):
    """http*://*nettiauto.com/*/*/*"""
    return fetch_nettiX(url, ['Vuosimallit', 'Mittarilukema', 'Moottori', 'Vaihteisto', 'Vetotapa'])


# TODO: Update other nettiX handlers


def _handle_nettivene(url):
    """http*://*nettivene.com/*/*/*"""
    return fetch_nettiX(url, ['Vuosimalli', 'Runkomateriaali', 'Pituus', 'Leveys'])


def _handle_nettimoto(url):
    """http*://*nettimoto.com/*/*/*"""
    return fetch_nettiX(url, ['Vuosimalli', 'Moottorin tilavuus', 'Mittarilukema', 'Tyyppi'])


def _handle_nettikaravaani(url):
    """http*://*nettikaravaani.com/*/*/*"""
    return fetch_nettiX(url, ['Vm./Rek. vuosi', 'Mittarilukema', 'Moottori', 'Vetotapa'])


def _handle_nettivaraosa(url):
    """http*://*nettivaraosa.com/*/*"""
    return fetch_nettiX(url, ['Varaosan osasto'])


def _handle_nettikone(url):
    """http*://*nettikone.com/*/*/*"""
    return fetch_nettiX(url, ['Vuosimalli', 'Osasto', 'Moottorin tilavuus', 'Mittarilukema', 'Polttoaine'])


def _handle_hitbox(url):
    """http*://*hitbox.tv/*"""
    # Blog and Help subdomains aren't implemented in Angular JS and works fine with default handler
    if re.match(r"https://(help|blog)\.hitbox\.tv/.*", url):
        return

    # Hitbox titles are populated by JavaScript so they return a useless "{{meta.title}}", don't show those
    elif not re.match(r"https://(www\.)?hitbox\.tv/([A-Za-z0-9]+)$", url):
        return False

    # For actual stream pages, let's fetch information via the hitbox API
    else:
        streamname = url.rsplit('/', 2)[2]
        api_url = 'https://api.hitbox.tv/media/live/%s' % streamname

        r = bot.get_url(api_url)

        try:
            data = r.json()
        except:
            log.debug('can\'t parse, probably wrong stream name')
            return 'Stream not found.'

        hitboxname = data['livestream'][0]['media_display_name']
        streamtitle = data['livestream'][0]['media_status']
        streamgame = data['livestream'][0]['category_name_short']
        streamlive = data['livestream'][0]['media_is_live']

        if streamgame is None:
            streamgame = ""
        else:
            streamgame = '[%s] ' % (streamgame)

        if streamlive == '1':
            return '%s%s - %s - LIVE' % (streamgame, hitboxname, streamtitle)
        else:
            return '%s%s - %s - OFFLINE' % (streamgame, hitboxname, streamtitle)

        return False


def _handle_google_play_music(url):
    """https://play.google.com/music/*"""
    bs = __get_bs(url)
    if not bs:
        return False

    title = bs.find('meta', {'property': 'og:title'})
    description = bs.find('meta', {'property': 'og:description'})
    if not title:
        return False
    elif title['content'] == description['content']:
        return False
    else:
        return title['content']


def _handle_steamstore(url):
    """https://store.steampowered.com/app/*"""

    # https://wiki.teamfortress.com/wiki/User:RJackson/StorefrontAPI
    api_url = "https://store.steampowered.com/api/appdetails/"
    app = re.match(r"https://store\.steampowered\.com\/app/(?P<id>\d+)", url)
    params = {'appids': app.group('id'), 'cc': 'fi'}

    r = bot.get_url(api_url, params=params)
    data = r.json()[app.group('id')]['data']

    name = data['name']
    if 'price_overview' in data:
        price = "%.2fe" % (float(data['price_overview']['final']) / 100)

        if data['price_overview']['discount_percent'] != 0:
            price += " (-%s%%)" % data['price_overview']['discount_percent']
    else:
        price = "Free to play"

    return "%s | %s" % (name, price)


def _handle_pythonorg(url):
    """http*://*python.org/*"""
    title = __get_title_tag(url)
    if title == 'Welcome to Python.org':
        return False

    return title.replace(' | Python.org', '')


def _handle_discogs(url):
    """https://*discogs.com/*"""

    apiurl = 'https://api.discogs.com/'
    headers = {'user-agent': 'pyfibot-urltitle'}

    title_formats = {
        'release': '{0[artists][0][name]} - {0[title]} - ({0[year]}) - {0[labels][0][catno]}',
        'artist': '{0[name]}',
        'label': '{0[name]}',
        'master': '{0[artists][0][name]} - {0[title]} - ({0[year]})',
    }

    m = re.match(
        r'http:\/\/(?:www\.)?discogs\.com\/(?:([A-Za-z0-9-]+)\/)?(release|master|artist|label|item|seller|user)\/(\d+|[A-Za-z0-9_.-]+)', url)

    if m:
        m = m.groups()
        if m[1] in title_formats:
            endpoint = '%ss/%s' % (m[1], m[2])
            data = bot.get_url('%s%s' % (apiurl, endpoint),
                               headers=headers).json()

            title = title_formats[m[1]].format(data)

        elif m[1] in ['seller', 'user']:
            endpoint = 'users/%s' % m[2]
            data = bot.get_url('%s%s' % (apiurl, endpoint),
                               headers=headers).json()

            title = ['{0[name]}']

            if data['num_for_sale'] > 0:
                plural = 's' if data['num_for_sale'] > 1 else ''
                title.append('{0[num_for_sale]} item%s for sale' % plural)

            if data['releases_rated'] > 10:
                title.append(
                    'Rating avg: {0[rating_avg]} (total {0[releases_rated]})')

            title = ' - '.join(title).format(data)

        elif m[0:2] == ['sell', 'item']:
            endpoint = 'marketplace/listings/%s' % m[2]
            data = bot.get_url('%s%s' % (apiurl, endpoint)).json()

            for field in ('condition', 'sleeve_condition'):
                if field in ['Generic', 'Not Graded', 'No Cover']:
                    data[field] = field
                else:
                    m = re.match(r'(?:\w+ )+\(([A-Z]{1,2}[+-]?)( or M-)?\)',
                                 data[field])
                    data[field] = m.group(1)

            fmt = ('{0[release][description]} [{0[price][value]}'
                   '{0[price][currency]} - ships from {0[ships_from]} - '
                   'Condition: {0[condition]}/{0[sleeve_condition]}]')

            title = fmt.format(data)

    if title:
        return title


def _handle_github(url):
    """http*://*github.com*"""
    return __get_title_tag(url)


def _handle_gitio(url):
    """http*://git.io*"""
    return __get_title_tag(url)


def _handle_gfycat(url):
    """http*://*gfycat.com/*"""

    api_url = "https://gfycat.com/cajax/get/%s"

    m = re.match(
        r"https?://(?:\w+\.)?gfycat.com/([\w]+)(?:\.gif|\.webm|\.mp4)?", url)
    if not m:
        return

    r = bot.get_url(api_url % m.group(1))
    j = r.json()['gfyItem']

    title = []
    if j['title']:
        title.append(j['title'])
    elif j['redditId']:
        try:
            baseurl = "https://www.reddit.com/r/%s/comments/%s/%s/.json"
            url = baseurl % (j['subreddit'], j['redditId'], j['redditIdText'])

            r = bot.get_url(url)
            data = r.json()[0]['data']['children'][0]['data']

            title.append(data['title'])
        except:
            pass

    if j['subreddit']:
        title.append("(/r/%s)" % j['subreddit'])

    title.append("%sx%s@%sfps" % (j['width'], j['height'], j['frameRate']))
    title.append("%s views" % j['views'])

    return " ".join(title)


# IGNORED TITLES
def _handle_travis(url):
    """http*://travis-ci.org/*"""
    return False


def _handle_ubuntupaste(url):
    """http*://paste.ubuntu.com/*"""
    return False


def _handle_poliisi(url):
    """http*://*poliisi.fi/*/tiedotteet/*"""
    return False
