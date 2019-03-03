import urllib


def command_oraakkeli(bot, user, channel, args):
    """Asks a question from the oracle (http://www.lintukoto.net/viihde/oraakkeli/)"""
    if not args:
        return
    args = urllib.quote_plus(args)
    r = getUrl(
        "http://www.lintukoto.net/viihde/oraakkeli/index.php?kysymys=%s&html=0" % args
    )
    return bot.say(channel, "Oraakkeli vastaa: %s" % r.text)
