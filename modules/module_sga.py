import re
import time, datetime

def command_sga(bot, user, channel, args):
    """Display Stargate: Atlantis airdate on The Movie Network (Canada)"""

    bs = getUrl("http://www.themovienetwork.ca/stargateatlantis/schedule.php").getBS()

    if not bs: return

    eps = bs.fetch('a', {'href':re.compile("details")})

    eplist = []

    for ep in eps:
        name = ep.next
        datestr = ep.next.next.next.next

        airtime = time.strptime(datestr, "%B %d - %I:%M %p")
        airdate = datetime.date(2006, airtime[1], airtime[2])

        eplist.append((airdate, name))

    # sort by airdate
    eplist.sort()

    # get some dates
    now = time.gmtime()
    nowdate = datetime.date(now[0], now[1], now[2])
    tomorrow = nowdate + datetime.timedelta(days=1)

    # find the next airing episode
    for airdate, ep in eplist:
        td = airdate-nowdate

        if td.days >= 0:
            if airdate == nowdate:
                airdate = "%s (Today)" % airdate
            elif airdate == tomorrow:
                airdate = "%s (Tomorrow)" % airdate
            else:
                airdate = "%s (%d days)" % (airdate, td.days)

            bot.say(channel, ep+" "+airdate)
            return

    bot.say(channel, "No unaired episodes found")
