"""Upload images encountered on channels to imgur.com"""

import urllib
import logging
import json
try:
    import oauth2 as oauth
    init_ok = True
except:
    init_ok = False

consumer = None
token = None


log = logging.getLogger("urltitle")


def init(bot):
    if not init_ok:
        log.error("Module not initialized, oauth2 library not found")
        return False
    global config
    global consumer_key, consumer_secret, oauth_token, oauth_token_secret
    global token, consumer
    try:
        config = config = bot.config.get("module_imgur", {})
    except KeyError:
        config = None

    consumer_key = config.get('consumer_key', '')
    consumer_secret = config.get('consumer_secret', '')
    oauth_token = config.get('oauth_token', '')
    oauth_token_secret = config.get('oauth_token_secret', '')

    token = oauth.Token(key=oauth_token, secret=oauth_token_secret)
    consumer = oauth.Consumer(key=consumer_key, secret=consumer_secret)


# Upload all files ending in jpg and gif
def handle_url(bot, user, channel, url, msg):
    if not init_ok:
        return
    # TODO: smarter checking, using content-type perhaps?
    if url.endswith(".jpg") or url.endswith(".gif"):
        #log.info(channel, upload_images([url]))
        images, link, aid = upload_images([url], user, channel)
        for image in images:
            log.info("Uploaded image http://imgur.com/%s by %s from %s to gallery %s" % (image, user, channel, link))


# Upload a page of images
def upload_gallery(url):
    from mechanize import Browser
    br = Browser()
    br.set_handle_robots(False)
    br.open(url)

    urls = set()

    for link in br.links(url_regex=".jpg$"):
        urls.add(link.url)

    upload_images(urls)


def upload_images(urls, user=None, channel=None):
    # uploaded images
    images = []

    client = oauth.Client(consumer, token)

    # Transload image(s) to imgur
    for url in urls:
        log.debug("Transloading %s" % url)

        metadata = {
            'image': url,
            'type': 'url',
            'caption': 'Original url: %s by: %s from: %s' % (url, user, channel)}

        resp, cont = client.request("http://api.imgur.com/2/account/images.json", "POST", body=urllib.urlencode(metadata))
        data = json.loads(cont)
        if resp.status != 200:
            log.debug(resp)
            errmsg = data['error']['message']
            log.error("Transload error for %s: %s " % (url, errmsg))
            if errmsg == "API limits exceeded":
                log.error("API limits exceeded, aborting uploads")
                return
            else:
                continue

        images.append(data['images']['image']['hash'])

    # check that the bot album exists
    resp, cont = client.request("http://api.imgur.com/2/account/albums.json", "GET")
    data = json.loads(cont)
    album = [album for album in data['albums'] if album['title'] == "Pyfibot"]
    if len(album) != 1:
        log.error("Album not found, please create it")
        return

    album = album[0]
    aid = album['id']
    link = album['anonymous_link']

    # add images to bot album
    resp, cont = client.request("http://api.imgur.com/2/account/albums/%s.json" % aid, "POST", body=urllib.urlencode({'add_images': ",".join(images)}))

    return (images, link, aid)
