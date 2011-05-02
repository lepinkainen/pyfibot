

import urllib

def command_oraakkeli(bot, user, channel, args):
    """Asks a question from the oracle (http://www.lintukoto.net/viihde/oraakkeli/)"""
    if not args: return

    args = urllib.quote_plus(args)

    answer = getUrl("http://www.lintukoto.net/viihde/oraakkeli/index.php?kysymys=%s&html=0" % args).getContent()

    answer = unicode(answer)
    answer = answer.encode("utf-8")
    
    return bot.say(channel, "Oraakkeli vastaa: %s" % answer)
