#!/usr/bin/python

from datetime import datetime, timedelta
import tvdb_api
import tvdb_exceptions
from operator import itemgetter

def command_ep(bot, user, channel, args):
    """Usage: ep <series name>"""
    t = tvdb_api.Tvdb()
    now = datetime.now()

    # prevent "Series '' not found"
    if not args: return

    try:
        series = t[args]
    except tvdb_exceptions.tvdb_shownotfound:
        bot.say(channel, "Series '%s' not found" % args)
        return

    episodes = []

    # find all episodes with airdate > now
    for season_no, season in series.items():
        for episode_no, episode in season.items():
            firstaired = episode['firstaired']
            if not firstaired:
                continue
            airdate = datetime.strptime(firstaired, "%Y-%m-%d")
            td = airdate - now
            # find the next unaired episode
            if td > timedelta(0, 0, 0):
                episodes.append(episode)

    # if any episodes were found, find out the one with airdate closest to now
    if episodes:
        # sort the list just in case it's out of order (specials are season 0)
        episodes = sorted(episodes, key=itemgetter('firstaired'))
        episode = episodes[0]
        td = datetime.strptime(episode['firstaired'], "%Y-%m-%d") - now

        season_ep = "%dx%02d" % (int(episode['combined_season']),int(episode['combined_episodenumber']))
        msg = "Next episode of %s %s '%s' airs %s (%d days)" % (series.data['seriesname'], season_ep, episode['episodename'], episode['firstaired'], td.days)
        bot.say(channel, msg.encode("UTF-8"))
    else:
        msg = "No new episode airdates found for %s" % series.data['seriesname']
        bot.say(channel, msg.encode("UTF-8"))

