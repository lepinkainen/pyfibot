"""Warns about large files"""

def handle_url(bot, user, channel, url):

    if channel == "#wow": return

    # inform about large files (over 5MB)
    size = getUrl(url).getSize()

    if not size: return
    
    size = size / 1024
    
    if size > 5:
        bot.say(channel, "File size: %s MB" % size)
