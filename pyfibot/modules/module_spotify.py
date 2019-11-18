"""
Parse spotify URLs
"""

from __future__ import unicode_literals, print_function, division
import re
import logging
import base64
import requests

log = logging.getLogger('spotify')


def get_token(client_id, client_secret):
    token = client_id + ":" + client_secret
    encoded_token = base64.b64encode(token)

    payload = {'grant_type': 'client_credentials'}
    headers = {'Authorization': 'Basic ' + encoded_token}
    auth_url = "https://accounts.spotify.com/api/token"
    r = requests.post(auth_url, payload, headers=headers)

    return r.json()['access_token']


def _handle_privmsg(bot, user, channel, args):
    """Grab Spotify URLs from the messages and handle them"""
    config = bot.config.get("module_spotify", {})

    m = re.match(r".*(https?:\/\/open.spotify.com\/|spotify:)(?P<item>album|artist|track|user[:\/]\S+[:\/]playlist)[:\/](?P<id>[a-zA-Z0-9]+)\/?.*", args)
    if not m:
        return None

    spotify_id = m.group('id')
    item = m.group('item').replace(':', '/').split('/')
    item[0] += 's'
    if item[0] == 'users':
        # All playlists seem to return 401 at the time, even the public ones
        return None

    bearer_token = get_token(config.get("client_id"), config.get("client_secret"))

    headers = {'Authorization': 'Bearer ' + bearer_token}
    apiurl = "https://api.spotify.com/v1/%s/%s" % ('/'.join(item), spotify_id)
    r = bot.get_url(apiurl, headers=headers)

    if r.status_code != 200:
        if r.status_code not in [401, 403]:
            log.warning('Spotify API returned %s while trying to fetch %s' % r.status_code, apiurl)
        print(r.json())
        return bot.say(channel, "Error: %s" % r.json()['error']['message'])

    data = r.json()

    title = '[Spotify] '
    if item[0] in ['albums', 'tracks']:
        artists = []
        for artist in data['artists']:
            artists.append(artist['name'])
        title += ', '.join(artists)

    if item[0] == 'albums':
        title += ' - %s (%s)' % (data['name'], data['release_date'])

    if item[0] == 'artists':
        title += data['name']
        genres_n = len(data['genres'])
        if genres_n > 0:
            genitive = 's' if genres_n > 1 else ''
            genres = data['genres'][0:4]
            more = ' +%s more' % genres_n - 5 if genres_n > 4 else ''

            title += ' (Genre%s: %s%s)' % (genitive, ', '.join(genres), more)

    if item[0] == 'tracks':
        title += ' - %s - %s' % (data['album']['name'], data['name'])

    return bot.say(channel, title)
