import urllib

def command_kv(bot, user, channel, args):
    """the Kimmo Virtanen -command"""
    baseurl = "http://batman.jypoly.fi/~77071/kannykka/irkki.php"
    urlargs = "action=ircquery&query=%s"
    urlargs = urlargs % urllib.quote(args)
    data = getUrl(baseurl + "?" + urlargs, nocache=True).getContent()
    bot.say(channel, "%s" % data)
