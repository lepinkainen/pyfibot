import urllib


def command_oraakkeli(bot, user, channel, args):
    """Asks a question from the oracle (http://www.lintukoto.net/viihde/oraakkeli/)"""
    if not args:
        return
    args = urllib.quote_plus(args)
    r = bot.get_url(
        "http://www.lintukoto.net/viihde/oraakkeli/index.php?kysymys=%s&html=0" % args
    )
    return bot.say(channel, "Lintukodon Oraakkeli vastaa: %s" % r.text)
