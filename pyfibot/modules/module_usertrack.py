# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import dataset
import logging
import re
from datetime import datetime


log = logging.getLogger('usertrack')
db = dataset.connect('sqlite:///databases/usertrack.db')


def get_table(bot, channel):
    return db['%s_%s' % (bot.network.alias, re.sub(r'&|#|!|\+', '', channel))]


def upsert_row(bot, channel, data, keys=['nick', 'ident', 'host']):
    table = get_table(bot, channel)
    table.upsert(data, keys)


def get_base_data(user):
    data = {
        'action_time': datetime.now()
    }

    data['nick'] = getNick(user)

    # For example kickee doesn't get full hostmask -> needs some work...
    try:
        data['ident'] = getIdent(user)
    except IndexError:
        pass
    try:
        data['host'] = getHost(user)
    except IndexError:
        pass

    return data


def handle_privmsg(bot, user, channel, message):
    data = get_base_data(user)
    data['last_action'] = 'message'
    data['last_message'] = message
    data['message_time'] = datetime.now()

    upsert_row(bot, channel, data)


def handle_userJoined(bot, user, channel):
    data = get_base_data(user)
    data['last_action'] = 'join'

    upsert_row(bot, channel, data)


def handle_userLeft(bot, user, channel, message):
    data = get_base_data(user)
    data['last_message'] = message
    if channel is not None:
        data['last_action'] = 'left'
        upsert_row(bot, channel, data)
    # QUIT returns the channel as None, loop through all tables, check if user exists and update it
    else:
        data['last_action'] = 'quit'
        for t in db.tables:
            table = db.load_table(t)
            res = table.find_one(nick=getNick(user), ident=getIdent(user), host=getHost(user))
            if res:
                data['id'] = res[0]
                table.update(data, ['id'])


def handle_userKicked(bot, kickee, channel, kicker, message):
    data = get_base_data(kickee)
    data['last_action'] = 'kicked by %s [%s]' % (getNick(kicker), message)
    # We don't get full info from kickee, need to update by nick only
    upsert_row(bot, channel, data, ['nick'])


def handle_userRenamed(bot, user, newnick):
    data = get_base_data(user)
    data['nick'] = newnick
    data['last_action'] = 'nick change'

    # loop through all the tables, if user exists, update nick to match
    for t in db.tables:
        table = db.load_table(t)
        res = table.find_one(nick=getNick(user), ident=getIdent(user), host=getHost(user))
        if res:
            data['id'] = res[0]
            table.update(data, ['id'])


def handle_action(bot, user, channel, data):
    print(data)
