from util import timeoutdict
import datetime
import time

# 2 Days, remove every 10 minutes
urlcache = timeoutdict.TimeoutDict(timeout=172800, pollinterval=600)

def handle_url(bot, user, channel, url):
    """Keep track of seen urls per channel"""

    if channel == "#wow": return

    urlid = "%s|%s" % (channel, url)

    # old link
    if urlcache.has_key(urlid):
        age = datetime.datetime.now() - urlcache[urlid]['time']

        agestr = ""
        
        if age.days > 0:
            agestr += "%d days " % age.days

        secs = age.seconds
        hours,minutes,seconds = secs//3600,secs//60%60,secs%60
        
        if hours > 0: agestr += "%d h " % hours
        if minutes > 0: agestr += "%d m " % minutes
        if seconds > 0: agestr += "%d s" % seconds

        if getNick(user) != getNick(urlcache[urlid]['nick']):
            bot.say(channel, "%s: wanha. (by %s %s ago)" % ( getNick(user),
                                                             getNick(urlcache[urlid]['nick']),
                                                             agestr))
    # new link
    else:
        urlcache[urlid] = {'nick':user,
                           'url':url,
                           'channel':channel,
                           'time':datetime.datetime.now()
                           }
