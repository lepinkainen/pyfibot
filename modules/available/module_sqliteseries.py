try:
    import sqlite3
except:
    import sqlite
import time
import datetime

# create table series (id INTEGER PRIMARY KEY, uid TEXT UNIQUE, serie TEXT, season INTEGER, episode INTEGER, title TEXT, airdate DATE);
# insert into series values(null, 'Alias', 1, 1, 'Pilot', date('2006-01-01'));
# select * from series where airdate = date('2006-01-02', '-1 day');
# select * from series where airdate = date('now', '-1 day');

def command_epinfo(bot, user, channel, args):
    """List series in the database"""
    
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
        bot.say(channel, "Usage: ep [today|yesterday|tomorrow] or [name of series]")
        return

    if args == "today":
        cur.execute("SELECT * FROM series WHERE airdate = date('now', 'localtime');")
        if cur.rowcount == 0:
            bot.say(channel, "No known releases today")
            return
    elif args == "yesterday":
        cur.execute("SELECT * FROM series WHERE airdate = date('now', 'localtime', '-1 day');")
        if cur.rowcount == 0:
            bot.say(channel, "No known releases yesterday")
            return
    elif args == "tomorrow":
        cur.execute("SELECT * FROM series WHERE airdate = date('now', 'localtime', '+1 day');")
        if cur.rowcount == 0:
            bot.say(channel, "No known releases tomorrow")
            return
    else:
        # try to find the serie
        cur.execute("SELECT * FROM series WHERE serie LIKE %s AND airdate >= date('now', 'localtime') LIMIT 1", ("%"+args+"%",))
        # nothing found, get more data from the web
        if cur.rowcount == 0:
            cur.execute("SELECT * FROM series WHERE serie LIKE %s", ("%"+args+"%",))
            if cur.rowcount == 0:
                bot.say(channel, "Series '%s' not found" % args) # TODO: add to 'wishlist' file or something?
                return
            else:
                bot.say(channel, "No unaired episodes of '%s' found" % args)
                return

    episodes = []
    # go through the results
    for (idno, uid, serie, season, episode, title, airdate) in cur:
        if episode < 10: episode = "0%d" % episode # pad ep with zeroes

        # YYYY-MM-DD -> datetime -> timedelta
        t = time.strptime(airdate, "%Y-%m-%d")
        ad = datetime.date(t.tm_year, t.tm_mon, t.tm_mday)
        now = datetime.date.today()
        tomorrow = now + datetime.timedelta(days=1)
        td = ad-now

        # change 0 and 1 to today & tomorrow, don't show date if we're asking stuff for a certain day
        airdatestr = ""
        if td.days >= 0:
            if ad == now:
                if args != "today": airdatestr = "on %s (Today)" % airdate
            elif ad == tomorrow:
                if args != "tomorrow": airdatestr = "on %s (Tomorrow)" % airdate
            else:
                airdatestr = "on %s (%d days)" % (airdate, td.days)
        
        episodes.append("%s %sx%s '%s' %s" % (serie, season, episode, title, airdatestr))

    bot.say(channel, "-- ".join(episodes))

    cur.close()
    con.close()
