try:
    import sqlite3
except:
    import sqlite
import time
import datetime

# create table urls (id TEXT UNIQUE, nick TEXT, url TEXT, channel TEXT, time int);

def handle_url(bot, user, channel, url):
    urlid = "%s|%s" % (channel, url)
    
    con = sqlite.connect("/home/shrike/pyfibot/modules/urls.db")
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
        hours,minutes,seconds = secs//3600,secs//60%60,secs%60
        
        if hours > 0: agestr += "%d h " % hours
        if minutes > 0: agestr += "%d m " % minutes
        if seconds > 0: agestr += "%d s" % seconds

        # don't alert for the same person
        if getNick(user) != getNick(userhost):
            if channel != "#wow":
                bot.say(channel, "%s: wanha. (by %s %s ago)" % ( getNick(user), getNick(userhost), agestr))
    else:
        cur.execute("INSERT INTO urls VALUES(%s, %s, %s, %s, %d)", (urlid, user, url, channel, int(time.time())));
        
    con.commit()
    cur.close()
    con.close()
