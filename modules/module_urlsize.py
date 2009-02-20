"""Warns about large files"""

def handle_url(bot, user, channel, url, msg):

    if channel == "#wow": return

    # inform about large files (over 5MB)
    size = getUrl(url).getSize()
    contentType = getUrl(url).getHeaders()['content-type']
    if not size: return
    
    size = size / 1024
    
    if size > 5:
        bot.say(channel, "File size: %s MB - Content-Type: %s" % (size, contentType))
