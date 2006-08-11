"""Display food lists from different sources"""

def command_lounas(bot, user, channel, args):
    """Usage: lounas <place>"""

    acceptlist = getUrl("http://batman.jypoly.fi/~77071/kannykka/lounas.php?action=ravintolat").getContent().split("\t")

    if not args or (args.split()[0] not in acceptlist):
        bot.say(channel, "Usage: lounas (%s)" % "|".join(acceptlist))
        return

    d = getUrl("http://batman.jypoly.fi/~77071/kannykka/lounas.php?action=ircbot&ravintola=%s" % args.split()[0]).getContent()

    data = d.split("\n")[2:-1]

    if d.startswith("Parse error"):
        bot.say(channel, d)
    else:
        menu = []
    
        for item in data:
            menu.append(item.lstrip("* ").rstrip(" "))

        bot.say(channel, " | ".join(menu))
