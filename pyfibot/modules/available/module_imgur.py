"""Upload images encountered on channels to imgur.com"""

import requests
import logging

log = logging.getLogger("urltitle")

album_id = ""
access_token = ""
refresh_token = ""

init_ok = False


def init(bot):
    try:
        config = config = bot.config.get("module_imgur", {})
    except KeyError:
        config = None

    global album_id
    album_id = config.get('album_id', '')
    global access_token
    access_token = config.get('access_token', '')
    global refresh_token
    refresh_token = config.get('refresh_token', '')

    global init_ok
    if access_token and refresh_token:
        init_ok = True


# Upload all files ending in jpg and gif
def handle_url(bot, user, channel, url, msg):
    if not init_ok:
        return
    # TODO: smarter checking, using content-type perhaps?
    if url.endswith(".jpg") or url.endswith(".gif"):
        #log.info(channel, upload_images([url]))
        responses = upload_images([url], user, channel)
        for r in responses:
            log.debug("Uploaded image http://imgur.com/%s by %s from %s to gallery" % (r['id'], user, channel))


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

    api = "https://api.imgur.com/3"

    headers = {"Authorization": "Bearer %s" % access_token}

    # Transload image(s) to imgur
    for url in urls:
        log.debug("Transloading %s" % url)

        metadata = {
            'image': url,
            'type': 'url',
            'album': album_id,
            'title': 'by: %s from: %s' % (user, channel),
            'description': 'Original url: %s' % (url)}

        r = requests.post("%s/upload" % api, headers=headers, data=metadata)

        if r.status_code != 200:
            log.error("Transload error for %s: %s " % (url, r.json()))
            # TODO: Handle token refresh
            # TODO: store tokens somewhere smart?

        images.append(r.json()['data'])

        log.info("%s uploaded to imgur gallery" % r.json()['data']['link'])

    return images


def _refresh_token(client_id, client_secret, refresh_token):
    r = requests.post("https://api.imgur.com/oauth2/token",
                      data={'client_id':client_id,
                            'client_secret':client_secret,
                            'grant_type':'refresh_token',
                            'refresh_token':refresh_token})

    new_access_token = r.json()['access_token']
    new_refresh_token = r.json()['refresh_token']
    log.info("Updated imgur access token for account %s" % r.json()['account_username'])

    return new_access_token, new_refresh_token
