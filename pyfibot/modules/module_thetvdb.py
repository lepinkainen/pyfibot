#!/usr/bin/python

from __future__ import unicode_literals, print_function, division
from datetime import datetime, timedelta

api_ok = True
try:
    import tvdb_api
    import tvdb_exceptions
except:
    print("tvdb api not available")
    api_ok = False
from operator import itemgetter

def command_ep(bot, user, channel, args):
    """Usage: ep <series name>"""
    if not api_ok: return
    t = tvdb_api.Tvdb()
    now = datetime.now()
    # one day resolution maximum
    now = now.replace(hour=0, minute=0, second=0, microsecond=0)

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
            # list all unaired episodes
            if td >= timedelta(0, 0, 0):
                future_episodes.append(episode)

    # if any future episodes were found, find out the one with airdate closest to now
    if future_episodes:
        # sort the list just in case it's out of order (specials are season 0)
        future_episodes = sorted(future_episodes, key=itemgetter('firstaired'))
        episode = future_episodes[0]
        td = datetime.strptime(episode['firstaired'], "%Y-%m-%d") - now

        if td.days == 1:
            airdate = "tomorrow"
        elif td.days > 1:
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
