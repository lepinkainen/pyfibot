from __future__ import unicode_literals, print_function, division
from xml.etree import ElementTree as ET
import requests
from datetime import datetime
from dateutil import tz
from dateutil.parser import parse as parse_dt


def find_series(name):
    """
    Finds the first show which hasn't ended.
    If no running shows are found, returns the first result.
    """
    r = requests.get(
        "http://services.tvrage.com/feeds/search.php", params={"show": name}
    )
    root = ET.fromstring(r.content)
    shows = root.findall("show")
    if shows is None:
        return

    for s in shows:
        if int(s.find("ended").text) == 0:
            return s.find("showid").text
    return shows[0].find("showid").text


def command_tvrage(bot, user, channel, args):
    """Fetch episode information from tvrage."""
    if not args:
        return bot.say(channel, "I need a show to search for!")

    show_id = find_series(args)
    if show_id is None:
        return bot.say(channel, "Series not found.")

    r = requests.get(
        "http://services.tvrage.com/feeds/episodeinfo.php", params={"sid": show_id}
    )
    show = ET.fromstring(r.content)
    if show is None:
        return bot.say(channel, "Series not found.")

    now = datetime.now().replace(tzinfo=tz.tzlocal())

    name = show.find("name").text
    link = show.find("link").text

    next_episode = show.find("nextepisode")
    if next_episode is not None:
        number = next_episode.find("number").text
        title = next_episode.find("title").text
        airtime = parse_dt(next_episode.find('airtime[@format="RFC3339"]').text)
        if airtime < now:
            return bot.say(
                channel,
                '%s - %s - "%s" aired %s ago <%s>'
                % (name, number, title, now - airtime, link),
            )
        return bot.say(
            channel,
            '%s - %s - "%s" airs in %s <%s>'
            % (name, number, title, airtime - now, link),
        )

    latest_episode = show.find("latestepisode")
    if latest_episode is None:
        return bot.say(channel, 'No episode information for "%s" <%s>' % (name, link))

    number = latest_episode.find("number").text
    title = latest_episode.find("title").text
    airtime = parse_dt(latest_episode.find("airdate").text).replace(tzinfo=tz.tzlocal())
    return bot.say(
        channel,
        '%s - %s - "%s" aired %s ago <%s>' % (name, number, title, now - airtime, link),
    )
