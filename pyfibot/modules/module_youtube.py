# -*- coding: utf-8 -*-
"""Search Youtube videos
Returns the first Youtube video found with the given keywords using Youtube API.
"""

from __future__ import unicode_literals, print_function, division


def command_youtube(bot, user, channel, args):
    """<message> Returns the first Youtube video found with the given keywords. Usage: .youtube sultans of swing"""
    search = args

    api_key = config.get('youtube_apikey', None)
    if api_key is None:
        log.warning(
            'Set API key in configuration to activate YouTube API titles')
        return None  # Can't do anything without key

    # replacing spaces with +
    search = search.replace(" ", "+")

    if len(search) > 0:

        api_url = "https://www.googleapis.com/youtube/v3/search?"
        params = {"q": search, "part": "snippet",
                  "type": "video", "key": api_key}

        r = bot.get_url(api_url, params=params)
        j = r.json()

        if j["items"][0]["id"]["videoId"]:
            return bot.say(
                channel,
                j["items"][0]["snippet"]["title"]
                + " - https://www.youtube.com/watch?v="
                + j["items"][0]["id"]["videoId"],
            )
        else:
            return bot.say(channel, "No results")
    else:
        return bot.say(channel, "No results")
