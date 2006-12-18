import sqlite
import time

# create table urls (id TEXT UNIQUE, nick TEXT, url TEXT, channel TEXT, time int);

def handle_url(bot, user, channel, url):
    print "SQLITEWANHA", user, channel, url

    urlid = "%s|%s" % (channel, url)
    

    con = sqlite.connect("/home/shrike/pyfibot/modules/urls.db")
    cur = con.cursor()
    cur.execute("SELECT * FROM urls WHERE id=%s", (urlid,))
    if cur.rowcount:
        id, nick, url, channel, timestamp = cur.fetchone()
        print "OLD URL", nick, timestamp
    else:
        print "NEW URL:", url
        cur.execute("INSERT INTO urls VALUES(%s, %s, %s, %s, %d)", (urlid, getNick(user), url, channel, int(time.time())));
        
    con.commit()
    cur.close()
    con.close()
