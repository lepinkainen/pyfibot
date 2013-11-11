"""Upload images encountered on channels to imgur.com"""

import requests
import logging
import os.path
import sys

log = logging.getLogger("imgur")

# Bot application ID
CLIENT_ID     = "a7a5d6bc929d48f"
CLIENT_SECRET = "57b1f90a12d4d72762b4b1bf644af5157f73fed5"

DATAFILE = os.path.join(sys.path[0], "modules", "imgur_auth.dat")

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

    # If refreshed tokens exist, get them from the file
    # else load seed values from config
    global access_token, refresh_token
    if os.path.exists(DATAFILE):
        f = open(DATAFILE, 'r')
        access_token = f.readline().strip()
        refresh_token = f.readline().strip()
        f.close()
        log.info("Loaded imgur credentials from %s" % DATAFILE)
    else:
        access_token = config.get('access_token', '')
        refresh_token = config.get('refresh_token', '')

    global init_ok
    if access_token and refresh_token:
        log.info("imgur auth tokens found")
        init_ok = True


# Upload all files ending in jpg and gif
def handle_url(bot, user, channel, url, msg):
    if not init_ok:
        return
    # TODO: smarter checking, using content-type perhaps?
    r = bot.get_url(url)
    content_type = r.headers['content-type'].split(';')[0]

    if content_type.startswith("image/"):
        #log.info(channel, upload_images([url]))
        responses = upload_images([url], user, channel)
        for r in responses:
            log.debug("Uploaded image http://imgur.com/%s by %s from %s to gallery" % (r.get('id', ''), user, channel))


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
    global access_token, refresh_token
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

        # error handling
        if r.status_code != 200:
            if r.status_code == 403 and \
               r.json()['data']['error'] == "The access token provided has expired.":
                access_token, refresh_token = _refresh_token(CLIENT_ID, CLIENT_SECRET, refresh_token)
                # recursive retry, kinda dangerous, but what the heck
                return upload_images([url], user, channel)
            else:
                log.error("Transload error for %s: %s " % (url, r.text))
                continue

        images.append(r.json()['data'])

        #log.info("%s uploaded to imgur gallery" % r.json()['data'].get('link', ''))

    return images


def _refresh_token(client_id, client_secret, refresh_token):
    r = requests.post("https://api.imgur.com/oauth2/token",
                      data={'client_id':client_id,
                            'client_secret':client_secret,
                            'grant_type':'refresh_token',
                            'refresh_token':refresh_token})

    if r.status_code == 200:
        new_access_token = r.json()['access_token']
        new_refresh_token = r.json()['refresh_token']
        log.info("Updated imgur access token for account %s" % r.json()['account_username'])

        f = open(DATAFILE, 'w')
        f.write(new_access_token+"\n")
        f.write(new_refresh_token+"\n")
        f.close()

        return new_access_token, new_refresh_token
    else:
        log.error("error refreshing tokens: %s", r.json())
        return None, None
