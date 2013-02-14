#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""pyfibot module_rss.py
@author Henri 'fgeek' Salo <henri@nerv.fi>, Tomi 'dmc' Nykänen
@copyright Copyright (c) 2010 Henri Salo
@licence BSD

$Id$
$HeadURL$
"""

from __future__ import unicode_literals, print_function, division
import sys
import os
import re
import urllib
import logging
import logging.handlers
import hashlib
from threading import Thread
import urllib2
import sqlite3

# import py2.6 json if available, fall back to simplejson
try:
    import json
except:
    try:
        import simplejson as json
    except ImportError, error:
        print('Error starting rss module: %s' % error)
        init_ok = False

try:
    import feedparser
    from twisted.internet import reactor
    import yaml
    import htmlentitydefs
    init_ok = True
except ImportError, error:
    print('Error starting rss module: %s' % error)
    init_ok = False

# Initialize logger
log = logging.getLogger('rss')

t = None
t2 = None
indexfeeds_callLater = None
output_callLater = None

# Config format:
# database: rss.db
# delays:
#   rss_sync: 300 #How often we synchronize rss-feeds (in seconds)
#   output: 7 #How often to output new elements to channels
# output_syntax: 0 #0 == feed_title: title - url, 1 == feed_title: title - shorturl, 2 == feed_title: title (id), 3 == feed_title: title, 4 == title
# bitly_login: #Needed if using shorturl format
# bitly_api_key: #Needed if using shorturl format

# With output_syntax #2 you could get url via .url <id>


def event_signedon(bot):
    """Starts rotators"""
    global indexfeeds_callLater, output_callLater
    if not init_ok:
        log.error("Config not ok, not starting rotators")
        return False
    if (empty_database > 0):
        if (indexfeeds_callLater != None):
            log.info("Stopping previous indexfeeds thread")
            indexfeeds_callLater.cancel()
        rotator_indexfeeds(bot, rssconfig["delays"]["rss_sync"])
        if (output_callLater != None):
            log.info("Stopping previous output thread")
            output_callLater.cancel()
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
    d.execute("CREATE TABLE IF NOT EXISTS feeds (id INTEGER PRIMARY KEY,feed_url TEXT,channel TEXT,feed_title TEXT, output_syntax_id INTEGER);")
    d.execute("CREATE TABLE IF NOT EXISTS titles_with_urls (id INTEGER PRIMARY KEY,feed_url TEXT,title TEXT,url TEXT,channel TEXT,printed INTEGER,hash TEXT UNIQUE);")
    db_conn.commit()
    #Check if database is empty
    global empty_database
    empty_database = d.execute("SELECT COUNT(*) FROM feeds").fetchone()[0]
    d.close()


def rss_addfeed(bot, user, channel, feed_url, output_syntax):
    """Adds RSS-feed to sqlite-database"""
    global empty_database
    try:
        feed_data = feedparser.parse(feed_url)
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

    d.execute("SELECT * FROM feeds WHERE feed_url = ? AND channel = ?", (feed_url, channel, ))
    already_on_db = d.fetchone()
    if already_on_db is None:
        data = [None, feed_url, channel, feed_title, output_syntax]
        d.execute("INSERT INTO feeds VALUES (?, ?, ?, ?, ?)", data)
        db_conn.commit()
        d.close()
        if (empty_database == 0):
            rotator_indexfeeds(bot, rssconfig["delays"]["rss_sync"])
            rotator_output(bot, rssconfig["delays"]["output"])
            empty_database = 1
            return bot.say(channel, "Url \"%s\" inserted to database." % feed_url)
    else:
        id = already_on_db[0]
        return bot.say(channel, "Url \"%s\" is already on database with ID: %i" % (feed_url, id))


def rss_delfeed(bot, user, channel, args):
    """Deletes RSS-feed from sqlite-database by given ID. Should have support for deletion using ID or feed's URL"""
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
    """Lists channels (or all) RSS-feeds from sqlite-database. Initialize connection to database-file"""
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


def rss_modify_feed_setting(bot, feed_ident, channel, target, tvalue):
    """Modifies feed's settings"""
    db_conn = sqlite3.connect(rssconfig["database"])
    d = db_conn.cursor()
    d.execute("SELECT id, feed_url FROM feeds WHERE id = ? OR feed_url = ?", (feed_ident, feed_ident,))
    row = d.fetchone()
    feed_url = row[1].encode("UTF-8")
    if (target == "title"):
        if (db_conn.execute("UPDATE feeds SET feed_title = ? WHERE id = ? OR feed_url = ? AND channel = ?", (tvalue, feed_ident, feed_ident, channel)).rowcount == 1):
            db_conn.commit()
            bot.say(channel, "Feed's (%s) title modified to \"%s\"" % (feed_url, tvalue.encode("UTF-8")))
    elif (target == "syntax"):
        if (db_conn.execute("UPDATE feeds SET output_syntax_id = ? WHERE id = ? OR feed_url = ? AND channel = ?", (tvalue, feed_ident, feed_ident, channel)).rowcount == 1):
            db_conn.commit()
            bot.say(channel, "Feed's (%s) output syntax modified to \"%s\"" % (feed_url, tvalue.encode("UTF-8")))
    else:
        bot.say(channel, "Invalid syntax! Usage: Add feed: .rss add <feed_url>, Delete feed: .rss del <feed_url/feed_id>, List feeds: .rss list, Change feed settings: .rss set <feed_id/feed_url> title/syntax <value>")
        d.close()


def rss_listfeeds(bot, user, channel, args):
    """Lists all RSS-feeds added to channel"""
    feeds = list_feeds(channel)
    for feed in feeds:
        bot.say(channel, "%s: %s" % (feed[0], feed[1]))


def command_rss(bot, user, channel, args):
    """Usage: Add feed: .rss add <feed_url>, Delete feed: .rss del <feed_url/feed_id>, List feeds: .rss list, Change feed settings: .rss set <feed_id/feed_url> title/syntax <value>"""
    try:
        args = args.split()
        subcommand = args[0]
        if (subcommand != "list"):
            feed_ident = args[1]
        if (isAdmin(user)):
            if (subcommand == "add"):
                if (len(args) > 2):
                    output_syntax = args[2]
                else:
                    output_syntax = rssconfig["output_syntax"]
                rss_addfeed(bot, user, channel, feed_ident, output_syntax)
            elif (subcommand == "del"):
                rss_delfeed(bot, user, channel, feed_ident)
            elif (subcommand == "list"):
                rss_listfeeds(bot, user, channel, None)
            elif (subcommand == "set"):
                target = args[2]
                tvalue = args[3].decode("UTF-8")
                if (target == "title"):
                    rss_modify_feed_setting(bot, feed_ident, channel, "title", tvalue)
                elif (target == "syntax"):
                    rss_modify_feed_setting(bot, feed_ident, channel, "syntax", tvalue)
            else:
                bot.say(channel, "Invalid syntax! Usage: Add feed: .rss add <feed_url>, Delete feed: .rss del <feed_url/feed_id>, List feeds: .rss list, Change feed settings: .rss set <feed_id/feed_url> title/syntax <value>")
    except IndexError:
        bot.say(channel, "Invalid syntax! Usage: Add feed: .rss add <feed_url>, Delete feed: .rss del <feed_url/feed_id>, List feeds: .rss list, Change feed settings: .rss set <feed_id/feed_url> title/syntax <value>")


def shorturl(url):
    try:
        # TODO: Use requests
        req = urllib2.Request("http://api.bit.ly/v3/shorten?%s" % urllib.urlencode({'longUrl': url, 'login': rssconfig["bitly_login"], 'apiKey': rssconfig["bitly_api_key"], 'format': 'json'}))
        results = json.loads(urllib2.urlopen(req).read())
        #log.debug("Shorturl: %s" % results['id'].encode("UTF-8"))
        if (results['status_code'] == 200):
            return results['data']['url'].encode("UTF-8")
        raise Exception("Error in function shorturl: %s" % results['status_txt'])
    except HTTPError, e:
        log.debug('Error in function shorturl (url => %s): %s' % (url, e.read()))


def unescape(text):
    """Unescape ugly wtf-8-hex-escaped chars."""
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text  # leave as is
    return re.sub("&#?\w+;", fixup, text)


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
        # Couldn't add entry twice
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
            feed_data.entries.reverse()
            for entry in feed_data.entries:
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
    """Prints feed's element url by given id"""
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
        # Database is already opened
        log.debug("Exception in command showurl: %s" % e)


def output(bot):
    """This function is launched from rotator to collect and announce new items from feeds to channel"""
    try:
        db_conn = sqlite3.connect(rssconfig["database"])
        d = db_conn.cursor()
        d.execute("SELECT * FROM titles_with_urls WHERE printed='0'")
        row = d.fetchone()
        if (row != None):
            log.debug("New row found for output")
            log.debug(row)

            id = row[0]
            feed_url = row[1]
            feed_output_syntax = d.execute("SELECT output_syntax_id FROM feeds WHERE feed_url = ?", (feed_url,)).fetchone()[0]
            if (feed_output_syntax == None):
                feed_output_syntax = rssconfig["output_syntax"]

            title = row[2]
            url = row[3]
            channel = row[4]

            title = unicode(unescape(title)).encode("UTF-8")
            channel = channel.encode("UTF-8")
            url = url.encode("UTF-8")

            feed_title = d.execute("SELECT feed_title from feeds where feed_url = ?", (feed_url,)).fetchone()[0].encode('UTF-8')

            if (feed_output_syntax == 0):
                bot.say(channel, "%s: %s – %s" % (feed_title, title, url))
            elif (feed_output_syntax == 1):
                bot.say(channel, "%s: %s – %s" % (feed_title, title, shorturl(url)))
            elif (feed_output_syntax == 2):
                bot.say(channel, "%s: %s (%i)" % (feed_title, title, id))
            elif (feed_output_syntax == 3):
                bot.say(channel, "%s: %s" % (feed_title, title))
            elif (feed_output_syntax == 4):
                bot.say(channel, "%s" % title)

            data = [url, channel]
            d.execute("UPDATE titles_with_urls SET printed=1 WHERE URL=? and channel=?", data)
            db_conn.commit()
            log.debug("output thread terminated cleanly")
    except StopIteration:
        pass
    except Exception, e:
        # Database is already opened
        log.debug("Exception in function output: %s" % e)
        pass


def rotator_indexfeeds(bot, delay):
    """Timer for methods/functions"""
    try:
        global t, t2, indexfeeds_callLater
        if (type(t2).__name__ == 'NoneType'):
            t = Thread(target=indexfeeds, args=(bot,))
            t.daemon = True
            t.start()
        elif t2.isAlive() == False:
            t = Thread(target=indexfeeds, args=(bot,))
            t.daemon = True
            t.start()
        if (empty_database > 0):
            indexfeeds_callLater = reactor.callLater(delay, rotator_indexfeeds, bot, delay)
    except Exception, e:
        print(e)


def rotator_output(bot, delay):
    """Timer for methods/functions"""
    try:
        global t, t2, output_callLater
        if t.isAlive() == False:
            t2 = Thread(target=output, args=(bot,))
            t2.daemon = True
            t2.start()
            t2.join()
        if (empty_database > 0):
            output_callLater = reactor.callLater(delay, rotator_output, bot, delay)
    except Exception, e:
        print(e)
