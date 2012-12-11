#!/usr/bin/python

from datetime import datetime, timedelta
import tvdb_api
import tvdb_exceptions

def command_ep(bot, user, channel, args):
    t = tvdb_api.Tvdb()
    now = datetime.now()

    try:
        series = t[args]
    except tvdb_exceptions.tvdb_shownotfound:
        bot.say(channel, "Series '%s' not found" % args)
        return

    latest_season = series[series.keys()[-1]]

    for episode_no, episode in latest_season.items():
        firstaired = episode['firstaired']

        if not firstaired:
            break

        airdate = datetime.strptime(firstaired, "%Y-%m-%d")
        td = airdate - now
        # find the next unaired episode
        if td > timedelta(0, 0, 0):
            msg = "Next episode of %s '%s' airs %s (%d days)" % (series.data['seriesname'], episode['episodename'], episode['firstaired'], td.days)
            bot.say(channel, msg.encode("UTF-8"))
            return

    msg = "No new episode airdates found for %s" % series.data['seriesname']
    bot.say(channel, msg.encode("UTF-8"))

