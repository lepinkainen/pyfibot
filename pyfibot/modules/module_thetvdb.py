#!/usr/bin/python

from datetime import datetime, timedelta
import tvdb_api


def command_ep(bot, user, channel, args):
    t = tvdb_api.Tvdb()
    now = datetime.now()

    series = t[args]
    latest_season = series[series.keys()[-1]]

    for episode_no in latest_season.keys():
        episode = latest_season[episode_no]
        firstaired = episode['firstaired']

        if not firstaired:
            msg = "No new episode airdates found for %s" % series.data['seriesname']
            bot.say(channel, msg.encode("UTF-8"))
            break

        airdate = datetime.strptime(firstaired, "%Y-%m-%d")
        td = airdate - now
        # find the next unaired episode
        if td > timedelta(0,0,0):
            msg = "Next episode of %s '%s' airs %s (%d days)" % (series.data['seriesname'], episode['episodename'], episode['firstaired'], td.days)
            bot.say(channel, msg.encode("UTF-8"))
            break
