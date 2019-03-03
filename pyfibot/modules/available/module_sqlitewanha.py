try:
    import sqlite3

    sqlite = sqlite3
except:
    import sqlite
import time
import datetime
import sys
import os.path

# create table urls (id TEXT UNIQUE, nick TEXT, url TEXT, channel TEXT, time int);


def init(bot):
    global config
    config = bot.config.get("module_sqlitewanha", None)


def handle_url(bot, user, channel, url, msg):
    if not config:
        return
    ret = None
    urlid = "%s|%s" % (channel, url)
    con = sqlite.connect(os.path.join(sys.path[0], "urls.sqlite"))
    cur = con.cursor()
    cur.execute("SELECT * FROM urls WHERE id=%s", (urlid,))
    if cur.rowcount:
        id, userhost, url, channel, timestamp = cur.fetchone()
        pastetime = datetime.datetime.fromtimestamp(timestamp)
        now = datetime.datetime.now()
        age = now - pastetime
        agestr = ""
        if age.days > 0:
            agestr += "%d days " % age.days
        secs = age.seconds
        hours, minutes, seconds = secs // 3600, secs // 60 % 60, secs % 60
        if hours > 0:
            agestr += "%d h " % hours
        if minutes > 0:
            agestr += "%d m " % minutes
        if seconds > 0:
            agestr += "%d s" % seconds
        # don't alert for the same person
        if getNick(user) != getNick(userhost) and channel not in config.get(
            "channels", []
        ):
            ret = bot.say(
                channel,
                "%s: wanha. (by %s %s ago)"
                % (getNick(user), getNick(userhost), agestr),
            )
    else:
        cur.execute(
            "INSERT INTO urls VALUES(%s, %s, %s, %s, %d)",
            (urlid, user, url, channel, int(time.time())),
        )
    con.commit()
    cur.close()
    con.close()
    return ret
