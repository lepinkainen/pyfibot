"""Upload images to imgur.com"""

import urllib
try:
    import json
    import oauth2 as oauth
    init_ok = True
except:
    init_ok = False

consumer_key = 'cbcbcaf338bc7b430428dc4b64500e7004c761bbd'
consumer_secret = '1e4f5bdff44ce1b2a8ec069d8a293991'
oauth_token = 'a0b19c8a764017234fedd83c095911d804c762172'
oauth_token_secret = '9b2033e1d48be6aca606bacba2901300'
consumer = None
token = None


def init(bot):
    if not init_ok:
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


def handle_url(bot, user, channel, url, msg):
    if init_ok and (url.endswith(".jpg") or url.endswith(".gif")):
        print channel, upload_images([url])


def upload_gallery(url):
    from mechanize import Browser
    br = Browser()
    br.set_handle_robots(False)
    br.open(url)

    urls = set()

    for link in br.links(url_regex=".jpg$"):
        urls.add(link.url)

    upload_images(urls)


def upload_images(urls):
    # uploaded images
    images = []

    client = oauth.Client(consumer, token)

    # Transload image(s) to imgur
    for url in urls:
        print "Transloading %s..." % url

        metadata = {
            'image': url, 
            'type': 'url',
            'caption': 'Original url: %s' % url}

        resp, cont = client.request("http://api.imgur.com/2/account/images.json", "POST", body=urllib.urlencode(metadata))
        data = json.loads(cont)
        if resp.status != 200:
            print resp
            errmsg = data['error']['message']
            print "Transload error for %s: %s " % (url, errmsg)
            if errmsg == "API limits exceeded":
                print "API limits exceeded, aborting uploads"
                return
            else:
                continue

        images.append(data['images']['image']['hash'])

    # check that the bot album exists
    resp, cont = client.request("http://api.imgur.com/2/account/albums.json", "GET")
    data = json.loads(cont)
    album = [album for album in data['albums'] if album['title'] == "Pyfibot"]
    if len(album) != 1:
        print "Album not found, please create it"
        return

    album = album[0]
    aid = album['id']
    link = album['anonymous_link']

    # add images to bot album
    resp, cont = client.request("http://api.imgur.com/2/account/albums/%s.json" % aid, "POST", body=urllib.urlencode({'add_images': ",".join(images)}))

    return "Images (%s) uploaded to %s (%s)" % (",".join(images), link, aid)
