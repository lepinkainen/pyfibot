import socket

def handle_userJoined(bot, user, channel):
    nick = getNick(user)
    userhost = user.split("!")[1]
    username, host = userhost.split("@")
    username = username.replace("~", "").replace("-", "")

    # known webchat hosts
    if host in ["webchat.xs4all.nl", "wwwirc.kapsi.fi", "webchat.mibbit.com"]:
        ip = parseWebchatIP(username)
        hostname = socket.getfqdn(ip)
        if hostname:
            return bot.say(channel, "%s is using webchat from %s -> %s" % (nick, ip, hostname))

def command_webchat(bot, user, channel, args):
    """Parse a webhcat hex ip to a domain"""
    ip = parseWebchatIP(args)
    if ip:
        hostname = socket.getfqdn(ip)
        return bot.say(channel, "webchat from %s" % hostname)
    else:
        return bot.say(channel, "%s: %s is not a valid webchat hex ip" % (getNick(user), args))

def parseWebchatIP(hexip):
    """Parse webchat hex-format ip to decimal ip"""
    ip = []

    for i in range(2,len(hexip)+2,2):
        try:
            dec = int(hexip[i-2:i], 16)
        except ValueError:
            return None
        ip.append(str(dec))

    return ".".join(ip)
