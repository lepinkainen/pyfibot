# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import dataset
import logging
import re
from datetime import datetime
from copy import deepcopy


log = logging.getLogger('usertrack')
db = dataset.connect('sqlite:///databases/usertrack.db')


def get_table(bot, channel):
    return db['%s_%s' % (bot.network.alias, re.sub(r'&|#|!|\+', '', channel))]


def upsert_row(bot, channel, data, keys=['nick', 'ident', 'host']):
    table = get_table(bot, channel)
    table.upsert(data, keys)


def get_base_data(user):
    data = {
        'nick': getNick(user),
        'action_time': datetime.now()
    }

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
    # if user == channel -> this is a query -> don't log
    if user == channel:
        return

    data = get_base_data(user)
    data['last_action'] = 'message'
    data['last_message'] = message
    data['message_time'] = datetime.now()

    upsert_row(bot, channel, data)


def handle_userJoined(bot, user, channel):
    data = get_base_data(user)
    data['last_action'] = 'join'

    upsert_row(bot, channel, data)

    table = get_table(bot, channel)
    if table.find_one(nick=getNick(user), ident=getIdent(user), host=getHost(user), op=True):
        log.info('auto-opping %s' % user)
        bot.mode(channel, True, 'o', user=getNick(user))


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
            if not t.startswith('%s_' % bot.network.alias):
                continue
            table = db.load_table(t)
            res = table.find_one(nick=getNick(user), ident=getIdent(user), host=getHost(user))
            if res:
                data['id'] = res['id']
                table.update(data, ['id'])


def handle_userKicked(bot, kickee, channel, kicker, message):
    data = get_base_data(kickee)
    data['last_action'] = 'kicked by %s [%s]' % (getNick(kicker), message)
    # We don't get full info from kickee, need to update by nick only
    upsert_row(bot, channel, data, ['nick'])

    # Update the kickers action also...
    data = get_base_data(kicker)
    data['last_action'] = 'kicked %s [%s]' % (getNick(kickee), message)
    upsert_row(bot, channel, data)


def handle_userRenamed(bot, user, newnick):
    nick = getNick(user)
    ident = getIdent(user)
    host = getHost(user)

    data = get_base_data(user)
    data['last_action'] = 'nick change from %s to %s' % (nick, newnick)

    # loop through all the tables, if user exists, update nick to match
    for t in db.tables:
        if not t.startswith('%s_' % bot.network.alias):
            continue

        table = db.load_table(t)

        # if row is found with new or old nick -> user is on the channel -> update
        if table.find_one(nick=nick, ident=ident, host=host) or \
           table.find_one(nick=newnick, ident=ident, host=host):
                # need to create a deep copy of data, as dataset seems to put changed fields back to data...
                # haven't found any documentation on this, so might be a bug?
                tmp_data = deepcopy(data)

                # update the old user
                table.upsert(tmp_data, ['nick', 'ident', 'host'])

                # update new user
                tmp_data = deepcopy(data)
                tmp_data['nick'] = newnick
                table.upsert(tmp_data, ['nick', 'ident', 'host'])


def handle_action(bot, user, channel, message):
    # if action is directed to bot instead of channel -> don't log
    if channel == bot.nickname:
        return

    data = get_base_data(user)
    data['last_action'] = 'action'
    data['last_message'] = message
    data['message_time'] = datetime.now()

    upsert_row(bot, channel, data)


def command_add_op(bot, user, channel, args):
    if not isAdmin(user) or user == channel or not args:
        return

    nick = args.strip()

    table = get_table(bot, channel)
    res = table.find_one(nick=nick)
    if not res:
        return bot.say(channel, 'user not found')

    data = {'id': res['id'], 'op': True}
    table.upsert(data, ['id'])
    return bot.say(channel, 'auto-opping %s!%s@%s' % (res['nick'], res['ident'], res['host']))


def command_remove_op(bot, user, channel, args):
    if not isAdmin(user) or user == channel or not args:
        return

    nick = args.strip()

    table = get_table(bot, channel)
    res = table.find_one(nick=nick)
    if not res:
        return bot.say(channel, 'user not found')

    data = {'id': res['id'], 'op': False}
    table.upsert(data, ['id'])
    return bot.say(channel, 'removed auto-op from %s!%s@%s' % (res['nick'], res['ident'], res['host']))


def command_op(bot, user, channel, args):
    table = get_table(bot, channel)
    if table.find_one(nick=getNick(user), ident=getIdent(user), host=getHost(user), op=True) or isAdmin(user):
        log.info('opping %s on %s by request' % (user, channel))
        bot.mode(channel, True, 'o', user=getNick(user))


def command_list_ops(bot, user, channel, args):
    if not isAdmin(user) or user == channel:
        return

    table = get_table(bot, channel)
    if args.strip() == 'full':
        ops = ', '.join(['%s!%s@%s' % (r['nick'], r['ident'], r['host']) for r in table.find(op=True)])
    else:
        ops = ', '.join(['%s' % r['nick'] for r in table.find(op=True)])
    return bot.say(channel, 'ops: %s' % ops)
