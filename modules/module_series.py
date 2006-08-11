
"""Serie episode finder"""

import os.path
import fnmatch
import time
import datetime
import urllib
import urlparse
import re

from odb2.filestr import Shelve

# a list of searchterms which to use when precaching the serie data
precache = ['NCIS', 'Boston Legal', 'battlestar galactica', 'veronica mars', 
'smallville', '24', 'lost', 'stargate sg-1', 'stargate atlantis', 'viva la bam', 'bullshit', 
'4400', 'mythbusters', 'house', 'last comic standing', 'deadwood', 'shield', 'blade -flashing', 
'the unit', 'prison break', 'bones', 'the simpsons', 'survivor']

cache_done=False

def _precache(bot):
    global series
    series = {}
    # precache certain objects
    bot.log("Filling episode cache")
    for seriename in precache:
        url = _search_serie(seriename)
        if url != None:
            _cache_serie(url)

    bot.log("Precached episodes for: [" + ", ".join(series.keys()) + "]")

def command_recache(bot, user, channel, args):
    """Refresh episode cache"""
    if not isAdmin(user): return
    
    now = time.gmtime()
    today = datetime.date(now[0], now[1], now[2])

    res = []
    
    for name, data in series.items():
        td = data['updatedate']-today
        if td.days > 7:
            url = _search_serie(seriename)
            _cache_serie(url)
            res.append(name)

    bot.say(channel, "Recached " + ", ".join(res))

def command_ep(bot, user, channel, args):
    """Shows the airdate for the next episode of a serie. Usage: ep <serie name>"""
    global cache_done

    if not cache_done:
        bot.say(channel, "Precaching episode data, this might take a while...")
        _precache(bot)
        cache_done = True
    
    now = time.gmtime()

    showdate = None
    # special arguments
    if args == "today":
        showdate = datetime.date(now[0], now[1], now[2])
    elif args == "yesterday":
        showdate = datetime.date(now[0], now[1], now[2]-1)
    elif args == "tomorrow":
        showdate = datetime.date(now[0], now[1], now[2]+1)

    if showdate:
        _show_date(bot, user, channel, args, showdate)
        return

    # search for episode in cache first
    res = _search_cache(args)
    if res:
        bot.say(channel, res)
        return

    # cache missed, get from web
    res = _search_serie(args)

    if res:
        # stuff data into cache
        _cache_serie(res)
        # ..and check cache again
        res = _search_cache(args)
        if res == None:
            bot.say(channel, "Could not find serie '%s'" % args)
        else:
            bot.say(channel, res)

def _cache_serie(url):
    """Add a series' data to the cache"""
    global series
    serie, epdata, updatedate = _get_seriedata(url)
    # on totally bogus searchs, seriename will be null, don't cache those
    if serie:
        series[serie] = {'epdata':epdata, 'updatedate':updatedate}    

def _get_seriedata(url):
    """Get serie name and all episodes from the given url

    @return serie name, episode data, last update day"""
    
    epRe=re.compile("(?P<no>[\d]+)\.[\s]+(?P<season>[\d]+)-[ ]?(?P<episode>[\d]+)[\s]+(?P<prodno>[\w-]+)?[\s]+(?P<date>[\d]{1,2} [\w]{3} [\d]{2})[\s]+<[^>]+>(?P<name>.*)</a>")
    
    filedata = getUrl(url).getContent()

    # tidy up the crappy html a bit
    r=[];
    for x in [x.split('\n') for x in filedata.split('\r')]:
        if x:
            r += x

    filedata = r
    r = []
    for line in filedata:
        if line:
            r.append(line.strip())

    filedata = r

    epdata = []

    seriename = getUrl(url).getBS().first("h1").renderContents()
    seriename = re.sub("<.*?>", "", seriename)

    for line in filedata:
        ###
        # find episodes
        ###
        m = epRe.match(line)
        if m:
            
            # convert datestring to gmtime format
            t = time.strptime(m.group('date'), '%d %b %y')
            
            # put episode data into a nifty dict
            data = {'epno'    : m.group('no'),
                    'season'  : int(m.group('season')),
                    'episode' : int(m.group('episode')),
                    'prodno'  : m.group('prodno'),
                    'airdate' : m.group('date'),
                    'airdate2': datetime.date(t[0], t[1], t[2]),
                    'epname'  : m.group('name')}
        
            epdata.append(data)

    return seriename, epdata, datetime.date.today()

def _show_date(bot, user, channel, args, date):
    """Show all episodes out on the given date"""
    # initialize some times

    found = {}

    # find all episodes out on the given date
    for seriename, data in series.items():
        for ep in data['epdata']:
            if ep['airdate2'] == date:
                if not found.has_key(seriename):
                    found[seriename] = []
                found[seriename].append(ep)

    # tidy up the results
    total = []
    
    for serie, eps in found.items():
        res = []
        res.append(serie)
        for ep in eps:
            res.append("%sx%02d '%s'" % (ep['season'], int(ep['episode']), ep['epname']))
        total.append(" ".join(res))

    if total:
        bot.say(channel, "Out %s: %s" % (args, " | ".join(total)))
    else:
        bot.say(channel, "No new eps out %s" % args)
        
def _search_cache(args):
    """Search episodes from cache and show next episode"""
    
    # don't search from empty cache
    if len(series.keys()) == 0: return None

    searchterm = "*%s*" % args.lower()

    # find matching series by name
    matches = fnmatch.filter([s.lower() for s in series.keys()], searchterm)

    if len(matches) > 1:
        # Multiple matches, checking for exact match
        exact_matches = [s.lower() for s in series.keys() if s.lower() == args]
        if exact_matches:
            matches = exact_matches

    if len(matches) > 1:        
        return "Multiple matches, pick one: %s" % matches
    elif len(matches) == 0:
        return None

    # get the correct data object
    for seriename, seriedata in series.items():
        if seriename.lower() == matches[0]:
            break

    # initialize some times
    now = time.gmtime()
    nowdate = datetime.date(now[0], now[1], now[2])
    yesterday = nowdate - datetime.timedelta(days=1)
    tomorrow = nowdate + datetime.timedelta(days=1)

    for data in seriedata['epdata']:
        td = data['airdate2']-nowdate
        
        if td.days >= 0:
            airdate = data['airdate']
            
            if data['airdate2'] == nowdate:
                airdate = "%s (Today)" % airdate
            elif data['airdate2'] == tomorrow:
                airdate = "%s (Tomorrow)" % airdate
            else:
                airdate = "%s (%d days)" % (airdate, td.days)
                
            return "Next on '%s': %sx%02d '%s' at %s" % (seriename, data['season'], int(data['episode']), data['epname'], airdate)
        
    return "Next on '%s': no unaired episodes found" % seriename

def _search_serie(searchterms):
    """Search for a serie and return its episode list page URL"""

    # google power
    if not searchterms: return
    
    url = "http://www.google.com/search?hl=en&q=site:epguides.com&q=%s"
    searchterms = urllib.quote(searchterms)
    bs = getUrl(url % searchterms).getBS()

    if not bs: return

    results = []

    # tidy up the search results
    for url in bs.fetch("a", {"href":re.compile("http://epguides.com/")}):
        url = url['href']

        # only add serie summary pages (don't end with .html)
        if url.endswith("/"):
            results.append(url)

    if not results: return None

    # lessee if we are smarter than the search engine (look for an exact match):
    # magle the searchterm string
    term = searchterms.replace(" ", "").lower()

    for url in results:
        seriename = urlparse.urlparse(url)[2].replace("/", "").lower()
        if term == seriename:
            return url

    # we weren't smarter, so just return what the search engine thought was best
    return results[0]
