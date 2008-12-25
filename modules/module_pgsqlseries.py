import time
import datetime
try:
    from pyPgSQL import PgSQL
except:
    pass

def init(botconfig):
    global config
    try:
        config = botconfig["module_pgsqlseries"]
    except KeyError:
        config = None
            
def command_ep(bot, user, channel, args):
    """Usage: sqlep [today|yesterday|tomorrow] or [seriename]"""
    if not config: return
    
    cx = PgSQL.connect(database=config["database"],
                       host=config["host"],
                       user=config["user"],
                       password=config["password"])
    cur = cx.cursor()

    if not args:
        bot.say(channel, "Usage: ep [today|yesterday|tomorrow] or [name of series]")
        return

    # handle special arguments
    if args in ["today", "tomorrow", "yesterday"]:
        cur.execute("SELECT * FROM series.episodes WHERE airdate = '%s';" % args)
        cur.fetchone()
        if cur.rowcount in [-1, 0]:
            bot.say(channel, "No known releases %s" % args)
            return
    else:
        # try to find the serie
        cur.execute("SELECT * FROM series.episodes WHERE series ~* %s AND airdate >= 'today' ORDER BY airdate LIMIT 1", (args,))
        cur.fetchone()
        # not found
        if cur.rowcount in [-1, 0]:
            # do we know anything like it?
            cur.execute("SELECT * FROM series.episodes WHERE series ~* %s", (args,))
            res = cur.fetchone()
            # no idea what you're trying to say, bub
            if cur.rowcount in [-1, 0]:
                bot.say(channel, "Series '%s' not found" % args)
                return
            # known serie, just no eps stored
            else:
                bot.say(channel, "No unaired episodes of '%s' found" % res['series'])
                return

    # rewind the cursor to counter the fetchone-hacks
    cur.rewind()
    episodes = []
    # go through the results
    for row in cur.fetchall():
        serie = row['series']
        season = row['season']
        episode = row['episode']
        title = row['title']
        airdate = row['airdate']
        if episode < 10: episode = "0%d" % episode # pad ep with zeroes

        ad = datetime.date.fromtimestamp(airdate.ticks())
        now = datetime.date.today()
        tomorrow = now + datetime.timedelta(days=1)
        td = ad-now
        # change 0 and 1 to today & tomorrow, don't show date if we're asking stuff for a certain day
        airdatestr = ""
        airdate = ad # use datetime instead of the postgres internal type
        if td.days >= 0:
            if ad == now:
                if args != "today": airdatestr = "on %s (Today)" % airdate
            elif ad == tomorrow:
                if args != "tomorrow": airdatestr = "on %s (Tomorrow)" % airdate
            else:
                airdatestr = "on %s (%d days)" % (airdate, td.days)
        
        episodes.append("%s %sx%s '%s' %s" % (serie, season, episode, title, airdatestr))

    bot.say(channel, "-- ".join(episodes))

    if not cur.closed: cur.close()
    cx.close()
