"""
Warns about large files

$Id$
$HeadURL$
"""
import requests

def handle_url(bot, user, channel, url, msg):
    """inform about large files (over 5MB)"""

    r = requests.head(url)
    size = r.headers['content-length']
    content_type = r.headers['content-type']
    if not content_type:
        content_type = "Unknown"
    if not size:
        return
    size = int(size) / 1024
    if size > 5:
        return bot.say(channel, "File size: %s MB - Content-Type: %s" % (size, content_type))
