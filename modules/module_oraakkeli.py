

import urllib

def command_oraakkeli(bot, user, channel, args):
    """Asks a question from the oracle (http://www.lintukoto.net/viihde/oraakkeli/)"""

    args = urllib.quote_plus(args)

    answer = getUrl("http://www.lintukoto.net/viihde/oraakkeli/index.php?kysymys=%s&html=0" % args).getContent()

    bot.say(channel, "Oraakkeli vastaa: %s" % answer)
