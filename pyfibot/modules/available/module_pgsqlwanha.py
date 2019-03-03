import datetime

try:
    from pyPgSQL import PgSQL
except:
    pass


# -- For postgresql
#
# CREATE TABLE pyfibot.urls
# (
#       url text NOT NULL,
#         channel character varying(255) NOT NULL,
#         userid character varying(255) NOT NULL,
#         "timestamp" timestamp without time zone NOT NULL,
#         id serial NOT NULL,
#         CONSTRAINT id PRIMARY KEY (id)
#       )
# WITHOUT OIDS;
# ALTER TABLE pyfibot.urls OWNER TO <user>;


def init(bot):
    global config
    config = bot.config.get("module_pgsqlwanha", None)


def handle_url(bot, user, channel, url, msg):
    return
    if not config:
        return
    cx = PgSQL.connect(
        database=config["database"],
        host=config["host"],
        user=config["user"],
        password=config["password"],
    )
    cur = cx.cursor()
    # find the oldest instance of given url on this channel
    cur.execute(
        "SELECT * FROM pyfibot.urls WHERE channel=%s AND url=%s ORDER BY timestamp;",
        (channel, url),
    )
    res = cur.fetchone()
    if res:
        url, channel, userhost, timestamp, urlid = res
        pastetime = datetime.datetime.fromtimestamp(res[3].ticks())
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
        if getNick(user) != getNick(userhost):
            if channel != "#wow":
                bot.say(
                    channel,
                    "%s: wanha. (by %s %s ago)"
                    % (getNick(user), getNick(userhost), agestr),
                )
    cur = cx.cursor()
    # always store URLs, this structure can handle it, sqlite can't
    cur.execute(
        "INSERT INTO pyfibot.urls (userid, channel, url, timestamp) VALUES(%s, %s, %s, NOW());",
        (user, channel, url),
    )
    cx.commit()
    cur.close()
    cx.close()
