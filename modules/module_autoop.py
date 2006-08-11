def handle_userJoined(bot, user, channel):
    if isAdmin(user):
        nick = getNick(user)
        bot.log("auto-opping %s" % user)
        bot.mode(channel, True, 'o', user=nick)
