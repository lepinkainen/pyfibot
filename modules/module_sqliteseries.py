import fnmatch
import time
import datetime
import urllib
import urlparse
import re
import sqlite

# create table series (id INTEGER PRIMARY KEY, uid TEXT UNIQUE, serie TEXT, season INTEGER, episode INTEGER, title TEXT, airdate DATE);
# insert into series values(null, 'Alias', 1, 1, 'Pilot', date('2006-01-01'));
# select * from series where airdate = date('2006-01-02', '-1 day');
# select * from series where airdate = date('now', '-1 day');

precache = ['NCIS', 'Boston Legal', 'battlestar galactica', 'veronica mars', 
'smallville', '24', 'lost', 'stargate sg-1', 'stargate atlantis', 'viva la bam', 'bullshit', 
'4400', 'mythbusters', 'house', 'last comic standing', 'deadwood', 'shield', 'blade -flashing', 
'the unit', 'prison break', 'bones', 'the simpsons', 'survivor']

CREATETABLE = "CREATE TABLE series (id INTEGER PRIMARY KEY, uid TEXT UNIQUE ON CONFLICT REPLACE, serie TEXT, season INTEGER, episode INTEGER, title TEXT, airdate DATE);"

def command_sqlcache(bot, user, channel, args):
    """Cache common series into the database"""
    if not isAdmin(user): return

    for seriename in precache:
        url = _search_serie(seriename)
        if url != None:
            _cache_serie(url)
    bot.say(channel, "Caching done")

def NOTinit():
    con = sqlite.connect("/home/shrike/pyfibot/modules/series.db");
    cur = con.cursor()
    cur.execute(CREATETABLE)
    cur.close()
    con.commit()
    con.close()

def command_epdel(bot, user, channel, args):
    if not isAdmin(user): return

    con = sqlite.connect("/home/shrike/pyfibot/modules/series.db");
    cur = con.cursor()
    cur.execute("DELETE FROM series WHERE serie='%s';" % args)
    cur.close()
    con.commit()
    con.close()

    bot.say(channel, "Done");

def command_epinfo(bot, user, channel, args):
    """List episodes in the database"""
    
    con = sqlite.connect("/home/shrike/pyfibot/modules/series.db");
    cur = con.cursor()

    cur.execute("SELECT DISTINCT serie FROM series");

    res = []
    for serie in cur:
        res.append(serie[0])

    res.sort()
    bot.say(channel, "Known series ("+str(len(res))+"): " + ", ".join(res))

    cur.close()
    con.close()

def command_ep(bot, user, channel, args):
    """Usage: sqlep [today|yesterday|tomorrow] or [seriename]"""
    
    con = sqlite.connect("/home/shrike/pyfibot/modules/series.db");
    cur = con.cursor()

    if not args:
        bot.say(channel, "Usage: sqlep [today|yesterday|tomorrow] or [seriename]")
        return

    if args == "today":
        cur.execute("SELECT * FROM series WHERE airdate = date('now');")
        if cur.rowcount == 0:
            bot.say(channel, "No known releases today")
            return
    elif args == "yesterday":
        modifier = "-1 day"
        cur.execute("SELECT * FROM series WHERE airdate = date('now', '-1 day');")
        if cur.rowcount == 0:
            bot.say(channel, "No known releases yesterday")
            return
    elif args == "tomorrow":
        modifier = "+1 day"
        cur.execute("SELECT * FROM series WHERE airdate = date('now', '+1 day');")
        if cur.rowcount == 0:
            bot.say(channel, "No known releases tomorrow")
            return
    else:
        # try to find the serie
        cur.execute("SELECT * FROM series WHERE serie LIKE %s AND airdate > date('now') LIMIT 1", ("%"+args+"%",))
        # nothing found, get more data from the web
        if cur.rowcount == 0:
            url = _search_serie(args)
            if url != None:
                _cache_serie(url)
                cur.execute("SELECT * FROM series WHERE serie LIKE %s AND airdate > date('now') LIMIT 1", ("%"+args+"%",))
                # still nothing found, give up
                if cur.rowcount == 0:
                    bot.say(channel, "No future episodes of '%s' found" % args)
                    return
    
    for (id, uid, serie, season, episode, title, airdate) in cur:
        if episode < 10: episode = "0%d" % episode # pad ep with zeroes

        # YYYY-MM-DD -> datetime -> timedelta
        t = time.strptime(airdate, "%Y-%m-%d")
        ad = datetime.date(t.tm_year, t.tm_mon, t.tm_mday)
        now = datetime.date.today()
        tomorrow = now + datetime.timedelta(days=1)
        td = ad-now

        if ad == now:
            airdate = "%s (Today)" % airdate
        elif ad == tomorrow:
            airdate = "%s (Tomorrow)" % airdate
        else:
            airdate = "%s (%d days)" % (airdate, td.days)
        
        #bot.say(channel, "Next episode on %s %sx%s '%s' on %s" % (serie, season, episode, title, airdate))
        msg = "Next episode on %s %sx%s '%s' at %s" % (serie, season, episode, title, airdate)
        bot.say(channel, msg)

    cur.close()
    con.close()

def _cache_serie(url):
    """Parse the seriedata from the internets into sqlite"""
    
    serie, epdata, updatedate = _get_seriedata(url)
    con = sqlite.connect("/home/shrike/pyfibot/modules/series.db");
    
    for episode in epdata:
        episode['epname'] = episode['epname'].replace("'", "pier")
        cur = con.cursor()
        uid = "%s%d%d" % (serie, episode['season'], episode['episode'])
        cur.execute("INSERT INTO series (uid, serie, season, episode, title, airdate) VALUES (%s, %s, %d, %d, %s, date(%s));", (uid, serie, episode['season'], episode['episode'], episode['epname'], episode['airdate2'].strftime("%Y-%m-%d")))
        cur.close()

    # Commit & close
    con.commit()
    con.close()

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
    # mangle the searchterm string
    term = searchterms.replace(" ", "").lower()

    for url in results:
        seriename = urlparse.urlparse(url)[2].replace("/", "").lower()
        if term == seriename:
            return url

    # we weren't smarter, so just return what the search engine thought was best
    return results[0]

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
