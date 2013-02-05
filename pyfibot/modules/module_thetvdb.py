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

    future_episodes = []
    all_episodes = []

    # find all episodes with airdate > now
    for season_no, season in series.items():
        for episode_no, episode in season.items():
            firstaired = episode['firstaired']
            if not firstaired:
                continue
            airdate = datetime.strptime(firstaired, "%Y-%m-%d")
            td = airdate - now

            all_episodes.append(episode)
            # find the next unaired episode
            if td > timedelta(0, 0, 0):
                future_episodes.append(episode)

    # if any episodes were found, find out the one with airdate closest to now
    if future_episodes:
        # sort the list just in case it's out of order (specials are season 0)
        future_episodes = sorted(future_episodes, key=itemgetter('firstaired'))
        episode = future_episodes[0]
        td = datetime.strptime(episode['firstaired'], "%Y-%m-%d") - now

        if td.days > 0:
            airdate = "%s (%d days)" % (episode['firstaired'], td.days)
        else:
            airdate = "today"

        season_ep = "%dx%02d" % (int(episode['combined_season']),int(episode['combined_episodenumber']))
        msg = "Next episode of %s %s '%s' airs %s" % (series.data['seriesname'], season_ep, episode['episodename'], airdate)
    # no future episodes found, show the latest one
    elif all_episodes:
        # find latst episode of the show
        all_episodes = sorted(all_episodes, key=itemgetter('firstaired'))
        episode = all_episodes[-1]

        td = now - datetime.strptime(episode['firstaired'], "%Y-%m-%d")
        airdate = "%s (%d days ago)" % (episode['firstaired'], td.days)

        season_ep = "%dx%02d" % (int(episode['combined_season']),int(episode['combined_episodenumber']))
        msg = "Latest episode of %s %s '%s' aired %s" % (series.data['seriesname'], season_ep, episode['episodename'], airdate)
    else:
        msg = "No new or past episode airdates found for %s" % series.data['seriesname']

    bot.say(channel, msg.encode("UTF-8"))
