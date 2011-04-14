#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""pyfibot BETA module_rss.py
@author Henri 'fgeek' Salo <henri@nerv.fi>, Tomi 'dmc' Nykänen
@copyright Copyright (c) 2010 Henri Salo
@licence BSD
"""

import sys
import os
import re
import urllib
import logging
import logging.handlers
import hashlib
from threading import Thread

try:
    import feedparser
    import sqlite3
    from twisted.internet import reactor
    import yaml
    init_ok = True
except ImportError, error:
    print 'Error starting rss module: ',error
    init_ok = False

# Initialize logger
log = logging.getLogger('rss')

t = None
t2 = None

# Config format:
# database: rss.db
# delays:
#   rss_sync: 300 #How often we synchronize rss-feeds (in seconds)
#   output: 7 #How often to output new elements to channels
# output_syntax: 0 #0 == feed_title: title - url, 1 == feed_title: title - shorturl, 2 == feed_title: title (id)

# With output_syntax #2 you could get url via .url <id>

def event_signedon(bot):
    """Starts rotators"""
    if not init_ok: 
        log.error("Config not ok, not starting rotators")
        return False

    global delay
    global output_dealy

    rotator_indexfeeds(bot, rssconfig["delays"]["rss_sync"])
    rotator_output(bot, rssconfig["delays"]["output"])

def init(botconfig):
    """Creates database if it doesn't exist"""
    if not init_ok: 
        log.error("Config not ok, skipping init")
        return False

    global rssconfig
    # Read configuration
    configfile = os.path.join(sys.path[0], 'modules', 'module_rss.conf')
    rssconfig = yaml.load(file(configfile))

    db_conn = sqlite3.connect(rssconfig["database"])
    d = db_conn.cursor()
    d.execute("CREATE TABLE IF NOT EXISTS feeds (id INTEGER PRIMARY KEY,feed_url TEXT,channel TEXT,feed_title TEXT);")
    d.execute("CREATE TABLE IF NOT EXISTS titles_with_urls (id INTEGER PRIMARY KEY,feed_url TEXT,title TEXT,url TEXT,channel TEXT,printed INTEGER,hash TEXT UNIQUE);")
    db_conn.commit()
    d.close()
    
def rss_addfeed(bot, user, channel, args):
    """Adds RSS-feed to sqlite-database"""
    url = args
    try:
        feed_data = feedparser.parse(url)
        feed_title = feed_data['feed']['title']
    except KeyError, e:
        return bot.say(channel, "Nothing inserted to database. Probably you mistyped URL?")
    """Initialize connection to database-file"""
    db_conn = sqlite3.connect(rssconfig["database"])
    d = db_conn.cursor()

    """Lets create scheme if the database-file does not exist"""
    try:
        fileinfo = os.stat(rssconfig["database"])

        if not os.path.isfile(rssconfig["database"]) or fileinfo.st_size == 0:
            # TODO: Update schema creation after database schema is ready
            d.execute("CREATE TABLE feeds int primary key unique, url text)")
            db_conn.commit()
            bot.say(channel, "Database \"%s\" created." % rssconfig["database"])
    except Exception, e:
        bot.say(channel, "Error: %s" % e)
        
    d.execute("SELECT * FROM feeds WHERE feed_url = ? AND channel = ?", (url, channel, ))
    already_on_db = d.fetchone()
    if already_on_db is None:
            data = [None, url, channel, feed_title]
            d.execute("INSERT INTO feeds VALUES (?, ?, ?, ?)", data)
            db_conn.commit()
            d.close()
            return bot.say(channel, "Url \"%s\" inserted to database." % url)
    else:
        id = already_on_db[0] 
        return bot.say(channel, "Url \"%s\" is already on database with ID: %i" % (url, id))

def rss_delfeed(bot, user, channel, args):
    """Deletes RSS-feed from sqlite-database by given ID"""
    """Should have support for deletion using ID or feed's URL"""
    db_conn = sqlite3.connect(rssconfig["database"])
    d = db_conn.cursor()

    d.execute("SELECT id, feed_url, channel FROM feeds WHERE id = ? OR feed_url = ?", (args, args,))
    row = d.fetchone()
    feed_url = row[1]
    if (db_conn.execute("DELETE FROM feeds WHERE channel = ? AND id = ? OR channel = ? AND feed_url = ?", (channel, args, channel, args)).rowcount == 1):
        db_conn.commit()
        bot.say(channel, "Feed %s deleted successfully" % feed_url.encode("UTF-8"))
    d.close()

def list_feeds(channel):
    """Lists channels (or all) RSS-feeds from sqlite-database"""

    """Initialize connection to database-file"""
    db_conn = sqlite3.connect(rssconfig["database"])
    d = db_conn.cursor()

    feeds = []
    if (channel == -1):
        d.execute("SELECT id, feed_url, channel FROM feeds ORDER BY id")
    else:
        d.execute("SELECT id, feed_url, channel FROM feeds WHERE channel = ? ORDER BY id", (channel,))
    for row in d:
        id = row[0]
        feed_url = row[1]
        feed_url = feed_url.encode('UTF-8')
        channel = row[2]
        data = [id, feed_url, channel]
        feeds.append(data)
    d.close()
    return feeds

def rss_listfeeds(bot, user, channel, args):
    """Lists all RSS-feeds added to channel"""
    feeds = list_feeds(channel)
    for feed in feeds:
        bot.say(channel, "%s: %s" % (feed[0], feed[1]))

def command_rss(bot, user, channel, args):
    """Usage: Add feed: .rss add <feed_url>, Delete feed: .rss del <feed_url/feed_id>, List feeds: .rss list"""
    try:
        args = args.split()
        subcommand = args[0]
        if (subcommand != "list"): feed_ident = args[1]
        if (isAdmin(user)):
            if (subcommand == "add"):
                rss_addfeed(bot, user, channel, feed_ident)
            elif (subcommand == "del"):
                rss_delfeed(bot, user, channel, feed_ident)
            elif (subcommand == "list"):
                rss_listfeeds(bot, user, channel, None)
            else:
                bot.say(channel, "Invalid syntax! Usage: Add feed: .rss add <feed_url>, Delete feed: .rss del <feed_url/feed_id>, List feeds: .rss list")
    except IndexError:
        bot.say(channel, "Invalid syntax! Usage: Add feed: .rss add <feed_url>, Delete feed: .rss del <feed_url/feed_id>, List feeds: .rss list") 

def shorturl(url):
    params = urllib.urlencode({'create': url})
    shorturl = urllib.urlopen("http://href.fi/api.php?%s" % params)
    return shorturl.read()

def remove_html_tags(data):
    p = re.compile(r'<.*?>')
    return p.sub('', data)

def sqlite_add_item(bot, feed_url, title, url, channel, cleanup):
    """Adds item with feed-url, title, url, channel and marks it as non-printed"""
    if not feed_url and title and url:
        log.debug('Arguments missing in sqlite_add_item.')
        return
    try:
        db_conn = sqlite3.connect(rssconfig["database"])
        d = db_conn.cursor()
        hash_string = url + "?channel=" + channel
        data = [None, feed_url, title, url, channel, cleanup, hashlib.md5(hash_string).hexdigest()]
        d.execute("INSERT INTO titles_with_urls VALUES (?, ?, ?, ?, ?, ?, ?)", data)
        log.info('Added title \"%s\" with URL \"%s\" (%s) to channel %s to database.' % (title, url, feed_url, channel))
        id = d.lastrowid
        db_conn.commit()
        db_conn.close()
    except sqlite3.IntegrityError, e:
        return
    except Exception, e:
        # Database is already opened
        log.debug('Error in sqlite_add_item: %s' % e)
        pass

def indexfeeds(bot):
    """Updates all RSS-feeds found on database and outputs new elements"""
    try:
	cleanup = 0
        log.debug("indexfeeds thread started")
        db_conn = sqlite3.connect(rssconfig["database"])
        d = db_conn.cursor()
	
        # If table is removed, then create a new one
        titles_table_exists = d.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='titles_with_urls'").fetchone()
	if (titles_table_exists[0] == 0):
            init(None)
            #cleanup = 1
	# If titles table is empty, insert new feed elements as "printed", so bot won't flood on startup
	#titles_count = d.execute("SELECT count(*) FROM titles_with_urls").fetchone()
        #if (titles_count[0] == 0):
        #    cleanup = 1

        # Let's count all rows to index
        rowcount = 0
        rows = d.execute("SELECT id, feed_url, channel FROM feeds ORDER BY id")
        for row in rows:
            rowcount = rowcount + 1
        log.debug('Feed count is: %i' % rowcount)
        feeds = list_feeds(-1)
        for feed in feeds:
            id = feed[0]
            feed_url = feed[1]
            log.debug('Indexing feed: %s' % feed_url)
            channel = feed[2]
            # If first run of current feed, insert new elements as "printed" so bot won't flood whole feed on startup/insert
            cleanup = 0
            titles_count = d.execute("SELECT count(*) FROM titles_with_urls WHERE feed_url = ?", (feed_url,)).fetchone()
            if (titles_count[0] == 0):
                cleanup = 1

            feed_data = feedparser.parse(feed_url)
            sorted_entries = sorted(feed_data.entries, key=lambda entry: entry["date_parsed"])
            for entry in sorted_entries:
                try:
                    title = remove_html_tags(entry['title'])
                    url = entry['link']
                    sqlite_add_item(bot, feed_url, title, url, channel, cleanup)
                except KeyError, e:
                    log.debug('indexfeeds: Keyerror %s' % e)
                except Exception, e:
                    log.debug('indexfeeds first: Exception %s' % e)
        db_conn.close()
        log.debug("indexfeeds thread terminated")
    except Exception, e:
        log.debug('Error in indexfeeds: %s', e)

def command_url(bot, user, channel, args):
    """Prints feed elements url by given id"""
    id = args
    try:
        db_conn = sqlite3.connect(rssconfig["database"])
        d = db_conn.cursor()
        d.execute("SELECT * FROM titles_with_urls WHERE id = ?", (id,))
        row = d.fetchone()
        if (row != None):
            id = row[0]
            feed_url = row[1]
            title = row[2]
            url = row[3]
            channel = row[4].encode("UTF-8")
            url = url.encode("UTF-8")
            bot.say(channel, "%s" % (url))
    except Exception, e:
        #Database is already opened
        log.debug("Exception in command showurl: %s" % e)

def output(bot):
    """This function is launched from rotator to collect and announce new items from feeds to channel"""
    try:
        db_conn = sqlite3.connect(rssconfig["database"])
        d = db_conn.cursor()
        d.execute("SELECT * FROM titles_with_urls WHERE printed='0'")
        row = d.fetchone()
        if (row != None):
            id = row[0]
            feed_url = row[1]
            title = row[2]
            url = row[3]
            channel = row[4]
            title = title.encode("UTF-8")
            channel = channel.encode("UTF-8")
            url = url.encode("UTF-8")
            feed_title = d.execute("SELECT feed_title from feeds where feed_url = ?", (feed_url,)).fetchone()[0].encode('UTF-8')

            if (rssconfig["output_syntax"] == 0): 
                bot.say(channel, "%s: %s - %s" % (feed_title, title, url))
            elif (rssconfig["output_syntax"] == 1): 
                bot.say(channel, "%s: %s - %s" % (feed_title, title, shorturl(url)))
            elif (rssconfig["output_syntax"] == 2): 
                bot.say(channel, "%s: %s (%i)" % (feed_title, title, id))
            data = [url, channel]

            d.execute("UPDATE titles_with_urls SET printed=1 WHERE URL=? and channel=?", data)
            db_conn.commit()
            log.debug("output thread terminated cleanly")
    except StopIteration:
        pass
    except Exception, e:
        #Database is already opened
        log.debug("Exception in function output: %s" % e)
        pass

def rotator_indexfeeds(bot, delay):
    """Timer for methods/functions"""
    try:
        print "indexfeeds run"
        global t, t2
        if (type(t2).__name__ == 'NoneType'):
            t = Thread(target=indexfeeds, args=(bot,))
            t.daemon = True
            t.start()
        elif t2.isAlive() == False:
            t = Thread(target=indexfeeds, args=(bot,))
            t.daemon = True
            t.start()
        reactor.callLater(delay, rotator_indexfeeds, bot, delay)
    except Exception, e:
        print e

def rotator_output(bot, delay):
    """Timer for methods/functions"""
    try:
        global t, t2
        if t.isAlive() == False:
            t2 = Thread(target=output, args=(bot,))
            t2.daemon = True
            t2.start()
            t2.join()
        reactor.callLater(delay, rotator_output, bot, delay)
    except Exception, e:
        print e
