from util.BeautifulSoup import BeautifulSoup
from util.BeautifulSoup import BeautifulStoneSoup
import urllib2

def command_server(bot, user, channel, args):
    """Usage: server <servername> (no typo handling, so l2type)"""
    
    page = urllib2.urlopen("http://wow-europe.com/en/serverstatus/")
    soup = BeautifulSoup(page)
    status = [x.parent.previous.previous for x in soup('b', {"class":"smallBold", "style":"color: #234303;"}) if BeautifulStoneSoup(x.next, convertEntities=BeautifulStoneSoup.HTML_ENTITIES).contents[0].lower()==args.lower()]
    if len(status) == 0:
        bot.say(channel, "Uknown server %s" % args)
        return
    if status[0]['src'] == '/shared/wow-com/images/icons/serverstatus/downarrow.gif':
        bot.say(channel, "Server %s is down" % args)
    else:
        bot.say(channel, "Server %s is up" % args)

    #serverNames = [BeautifulStoneSoup(x.next, convertEntities=BeautifulStoneSoup.HTML_ENTITIES).contents[0] for x in soup('b', {"class":"smallBold", "style":"color: #234303;"})]

def command_bestserver(bot, user, channel, args):
    pass
