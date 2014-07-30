from __future__ import unicode_literals, print_function, division
import feedparser
import dataset
from twisted.internet.reactor import callLater
from threading import Thread
import twisted.internet.error
import logging


logger = logging.getLogger('module_rss')
DATABASE = dataset.connect('sqlite:///databases/rss.db')
updater = None
botref = None
config = {}


def init(bot):
    ''' Initialize updater '''
    global config
    global botref
    global updater
    global logger

    logger.info('RSS module initialized')
    botref = bot
    config = bot.config.get('rss', {})
    if updater:
        try:
            updater.cancel()
        except twisted.internet.error.AlreadyCalled:
            pass
        updater = None
    # As there's no signal if this is a rehash or restart
    # update feeds in 30 seconds
    updater = callLater(30, update_feeds)


def finalize():
    ''' Finalize updater (rehash etc) so we don't leave an updater running '''
    global updater
    global logger
    logger.info('RSS module finalized')
    if updater:
        try:
            updater.cancel()
        except twisted.internet.error.AlreadyCalled:
            pass
        updater = None


def get_feeds(db=None, **kwargs):
    ''' Get feeds from database '''
    if not db:
        db = DATABASE
    return [
        Feed(f['network'], f['channel'], f['id'], db=db)
        for f in list(db['feeds'].find(**kwargs))
    ]


def find_feed(network, channel, db=None, **kwargs):
    ''' Find specific feed from database '''
    if not db:
        db = DATABASE
    f = db['feeds'].find_one(network=network, channel=channel, **kwargs)
    if not f:
        return
    return Feed(f['network'], f['channel'], f['id'], db=db)


def add_feed(network, channel, url, db=None):
    ''' Add feed to database '''
    if not db:
        db = DATABASE
    f = Feed(network=network, channel=channel, url=url, db=db)
    return (f.initialized, f.read())


def remove_feed(network, channel, id, db=None):
    ''' Remove feed from database '''
    if not db:
        db = DATABASE
    f = find_feed(network=network, channel=channel, id=int(id), db=db)
    if not f:
        return
    f = f
    db['feeds'].delete(id=f.id)
    return f


def update_feeds(cancel=True, db=None, **kwargs):
    # from time import sleep
    ''' Update all feeds in the DB '''
    global config
    global updater
    global logger
    logger.info('Updating RSS feeds started')
    for f in get_feeds(db=db, **kwargs):
        Thread(target=f.update).start()

    # If we get a cancel, cancel the existing updater
    # and start a new one
    # NOTE: Not sure if needed, as atm cancel isn't used in any command...
    if cancel:
        try:
            updater.cancel()
        except twisted.internet.error.AlreadyCalled:
            pass
        updater = callLater(5 * 60, update_feeds)


def command_rss(bot, user, channel, args, db=None):
    commands = ['list', 'add', 'remove', 'latest', 'update']

    # Note: db -argument is only for tests...
    if not db:
        db = DATABASE

    args = args.split()
    if not args or args[0] not in commands:
        return bot.say(channel, 'rss: valid arguments are [%s]' % (', '.join(commands)))

    command = args[0]
    network = bot.network.alias

    # Get latest feed item from database
    # Not needed? mainly for debugging
    # Possibly useful for checking if feed still exists?
    if command == 'latest':
        if len(args) < 2:
            return bot.say(channel, 'syntax: ".latest id (from list)"')
        feed = find_feed(network=network, channel=channel, id=int(args[1]), db=db)
        if not feed:
            return bot.say(channel, 'feed not found, no action taken')
        item = feed.get_latest()
        if not item:
            return bot.say(channel, 'no items in feed')
        return bot.say(channel, feed.get_item_str(item))

    # List all feeds for current network && channel
    if command == 'list':
        feeds = get_feeds(network=network, channel=channel, db=db)
        if not feeds:
            return bot.say(channel, 'no feeds set up')

        for f in feeds:
            bot.say(channel, '%02i: %s <%s>' % (f.id, f.name, f.url))
        return

    # Rest of the commands are only for admins
    if not bot.factory.isAdmin(user):
        return bot.say(channel, 'only "latest" and "list" available for non-admins')

    # Add new feed for channel
    if command == 'add':
        if len(args) < 2:
            return bot.say(channel, 'syntax: ".add url"')
        init, items = add_feed(network, channel, url=args[1], db=db)
        if not init:
            return bot.say(channel, 'feed already added')
        return bot.say(channel, 'feed added with %i items' % len(items))

    # remove feed from channel
    if command == 'remove':
        if len(args) < 2:
            return bot.say(channel, 'syntax: ".remove id (from list)"')
        feed = remove_feed(network, channel, id=args[1], db=db)
        if not feed:
            return bot.say(channel, 'feed not found, no action taken')
        return bot.say(channel, 'feed "%s" <%s> removed' % (feed.name, feed.url))

    # If there's no args, update all feeds (even for other networks)
    # If arg exists, try to update the feed...
    if command == 'update':
        if len(args) < 2:
            bot.say(channel, 'feeds updating')
            update_feeds(db=db)
            return
        feed = find_feed(network, channel, id=int(args[1]), db=db)
        if not feed:
            return bot.say(channel, 'feed not found, no action taken')
        feed.update()
        return


class Feed(object):
    ''' Feed object to simplify feed handling '''
    def __init__(self, network, channel, id=None, url=None, db=None):
        # Not sure if (this complex) init is needed...
        self.id = id
        self.network = network
        self.channel = channel
        self.url = url
        self.db = db

        if url:
            self.url = url
        if not db:
            self.db = DATABASE
        self.initialized = False
        # load feed details from database
        self._get_feed_from_db()

    def __repr__(self):
        return '(%s, %s, %s)' % (self.url, self.channel, self.network)

    def __unicode__(self):
        return '%i - %s' % (self.id, self.url)

    def __init_feed(self):
        ''' Initialize databases for feed '''
        self.db['feeds'].insert({
            'network': self.network,
            'channel': self.channel,
            'url': self.url,
            'name': '',
        })
        # Update feed to match the created
        feed = self._get_feed_from_db()
        # Initialize item-database for feed
        self.__save_item({
            'title': 'PLACEHOLDER',
            'link': 'https://github.com/lepinkainen/pyfibot/',
            'printed': True,
        })
        self.initialized = True
        return feed

    def __get_items_tbl(self):
        ''' Get table for feeds items '''
        return self.db[('items_%i' % (self.id))]

    def __parse_feed(self):
        ''' Parse items from feed '''
        f = feedparser.parse(self.url)
        if self.initialized:
            self.update_feed_info({'name': f['channel']['title']})
        items = [{
            'title': i['title'],
            'link': i['link'],
        } for i in f['items']]
        return (f, items)

    def __save_item(self, item, table=None):
        ''' Save item to feeds database '''
        if table is None:
            table = self.__get_items_tbl()
        # If override is set or the item cannot be found, it's a new one
        if not table.find_one(title=item['title'], link=item['link']):
            # If printed isn't set, set it to the value in self.initialized (True, if initializing, else False)
            # This is to prevent flooding when adding a new feed...
            if 'printed' not in item:
                item['printed'] = self.initialized
            table.insert(item)

    def __mark_printed(self, item, table=None):
        ''' Mark item as printed '''
        if table is None:
            table = self.__get_items_tbl()
        table.update({'id': item['id'], 'printed': True}, ['id'])

    def _get_feed_from_db(self):
        ''' Get self from database '''
        feed = None
        if self.url and not self.id:
            feed = self.db['feeds'].find_one(network=self.network, channel=self.channel, url=self.url)
        if self.id:
            feed = self.db['feeds'].find_one(network=self.network, channel=self.channel, id=self.id)
        if not feed:
            feed = self.__init_feed()
        self.id = feed['id']
        self.network = feed['network']
        self.channel = feed['channel']
        self.url = feed['url']
        # TODO: Name could just be the domain part of url?
        self.name = feed['name']
        return feed

    def get_item_str(self, item):
        return '[%s] %s <%s>' % (''.join([c for c in self.name][0:18]), item['title'], item['link'])

    def get_latest(self):
        tbl = self.__get_items_tbl()
        items = [i for i in list(tbl.find(order_by='id'))]
        if not items:
            return
        return items[-1]

    def update_feed_info(self, data):
        ''' Update feed information '''
        data['id'] = self.id
        if 'url' in data:
            self.url = data['url']
        self.db['feeds'].update(data, ['id'])
        # Update self to match new...
        self._get_feed_from_db()

    def read(self):
        ''' Read new items from feed '''
        f, items = self.__parse_feed()
        # Get table -reference to speed up stuff...
        tbl = self.__get_items_tbl()
        # Save items in DB, saving takes care of duplicate checks
        for i in reversed(items):
            self.__save_item(i, tbl)
        # Set initialized to False, as we have read everything...
        self.initialized = False
        return items

    def get_new_items(self, mark_printed=False):
        ''' Get all items which are not marked as printed, if mark_printed is set, update printed also. '''
        tbl = self.__get_items_tbl()
        items = [i for i in list(tbl.find(printed=False))]
        if mark_printed:
            for i in items:
                self.__mark_printed(i, tbl)
        return items

    def update(self):
        global logger
        global botref

        # If botref isn't defined, bot isn't running, no need to run
        # (used for tests?)
        if not botref:
            return

        # Read all items for feed
        logger.info('Feed "%s" updating' % (self.name))
        self.read()
        # Get number of unprinted items (and don't mark as printed)
        items = self.get_new_items(False)
        logger.info('Feed "%s" updated with %i new items' % (self.name, len(items)))

        # If bot instance isn't found, don't print anything
        bot_instance = botref.find_bot_for_network(self.network)
        if not bot_instance:
            logger.error('Bot instance for "%s" not found, not printing' % (self.name))
            return

        logger.info('Printing new items for "%s"' % (self.name))
        # Get all new (not printed) items and print them
        items = self.get_new_items(True)
        for i in items:
            bot_instance.say(self.channel, self.get_item_str(i))


if __name__ == '__main__':
    f = Feed('ircnet', '#pyfibot', 'http://feeds.feedburner.com/ampparit-kaikki?format=xml')
    f.read()
    for i in f.get_new_items(True):
        print(i)
