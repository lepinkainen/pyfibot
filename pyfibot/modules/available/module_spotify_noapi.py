"""
Parse spotify URLs

A modified version of the original pyfibot spotify module

Spotify closed down the API and it needs authentication. This works around it by making a request to
an endpoint with a smartphone user-agent. It seems to yield more html-content from which to parse from

Use freely and at own risk. I am not viable for anything.

done in Jan 2018 by T-101 / Darklite ^ Primitive

"""

from __future__ import unicode_literals, print_function, division
import re
import json
import logging

from bs4 import BeautifulSoup

log = logging.getLogger("spotify")


def handle_privmsg(bot, user, channel, args):
    class SpotifyData(object):
        def __init__(self):
            self._data = None
            self.output = None

        @staticmethod
        def _parse_script_elements(scripts):
            """

           Selects the desired <script> element containing the desired json data

           """
            for script in scripts:
                if re.search(r"Spotify.Entity", script.string):
                    return re.sub(r"[\n\t]", "", script.string)

        @staticmethod
        def _ms_human_readable(ms):
            """

           Converts milliseconds into a tuple of (minutes, seconds)

           """
            minutes = int(ms / 60000)
            seconds = int((ms - minutes * 60000) / 1000)
            return minutes, seconds

        @property
        def data(self):
            return self._data

        @data.setter
        def data(self, value):
            """

           Takes a list of <script> elements, selects the desired one and morphs contents to a neat json dict

           """
            soup = BeautifulSoup(value, "html.parser")
            script = self._parse_script_elements(soup.find_all("script"))
            if script:
                element = re.search(r"Spotify.Entity = ({.*});", script).group(1)
                self._data = json.loads(element)

        @data.deleter
        def data(self):
            self._data = None
            self.data = None

        def parse(self, data, data_type):
            """

           Parse data, and set the .output parameter accordingly

           """

            self.data = data
            if not self.data:
                return

            if data_type == "track":
                artist = ", ".join(
                    [artist.get("name") for artist in self.data.get("artists")]
                )
                name = self.data.get("name")
                duration = self._ms_human_readable(int(self.data.get("duration_ms")))

                self.output = "\002[Spotify]\002 %s - %s [%sm%ss]" % (
                    artist,
                    name,
                    duration[0],
                    duration[1],
                )
                if self.data.get("album") and self.data.get("album").get("name"):
                    self.output += ' (from "%s")' % self.data.get("album").get("name")

            elif data_type == "album":
                artist = ", ".join(
                    [artist.get("name") for artist in self.data.get("artists")]
                )
                name = self.data.get("name")
                tracks = self.data.get("tracks").get("total")
                released = 0
                if re.match(r"\d{4}", self.data.get("release_date")):
                    released = re.match(r"\d{4}", self.data.get("release_date")).group()

                self.output = "\002[Spotify Album]\002 %s (%s, %s tracks) by %s" % (
                    name,
                    released,
                    tracks,
                    artist,
                )

            elif data_type == "artist":
                self.output = "\002[Spotify Artist]\002 %s" % self.data.get("name")

            elif data_type == "playlist":
                name = self.data.get("name")
                owner = self.data.get("owner").get("id")
                followers = self.data.get("followers").get("total")
                tracks = self.data.get("tracks").get("total")

                self.output = (
                    "\002[Spotify Playlist]\002 %s by %s (%s tracks, %s followers)"
                    % (name, owner, tracks, followers)
                )

            return self

    m = re.match(
        r".*(https?:\/\/open.spotify.com\/|spotify:)(?P<item>album|artist|track|user[:\/]\S+[:\/]playlist)[:\/](?P<id>[a-zA-Z0-9]+)\/?.*",
        args,
    )
    if not m:
        return None

    spotify_id = m.group("id")
    item = m.group("item").replace(":", "/").split("/")

    if item[-1] not in ("track", "album", "artist", "playlist"):
        bot.log("Given endpoint not yet supported")
        return

    r = re.search(r"(https?:\/\/\S+)", args)
    if r:
        url = r.group()
    elif item[-1] == "playlist":
        url = "https://open.spotify.com/user/%s/playlist/%s" % (item[1], spotify_id)
    else:
        url = "https://open.spotify.com/%s/%s" % (item[-1], spotify_id)

    user_agent = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0.1; SM-G900R4 Build/MMB29M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/55.0.2883.91 Mobile Safari/537.36"
    }
    r = bot.get_url(url=url, headers=user_agent)
    if r.status_code != 200:
        bot.log("module_spotify_noapi.py HTTP status code %s" % r.status_code)
        # bot.log("HTTP response %s" % r.content)
        return

    spotify_data = SpotifyData().parse(r.content, item[-1])

    if spotify_data.output:
        bot.say(channel, spotify_data.output)
