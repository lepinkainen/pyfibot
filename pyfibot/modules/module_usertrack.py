# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import dataset
import logging
import re
from datetime import datetime
from copy import deepcopy
import os


log = logging.getLogger('usertrack')

if not os.path.exists('databases'):
    os.makedirs('databases')
db = dataset.connect('sqlite:///databases/usertrack.db')


def get_table(bot, channel):
    ''' Returns table-instance from database.
    Database names are in format "networkalias_channel".
    Network alias is the name assigned to network in config.
    Channel is stripped from the &#!+ prepending the channel name. '''

    return db['%s_%s' % (bot.network.alias, re.sub(r'&|#|!|\+', '', channel))]


def upsert_row(bot, channel, data, keys=['nick', 'ident', 'host']):
    ''' Updates row to database.
    Default keys are nick, ident and host,
    which are normally present for data received by get_base_data -function. '''

    table = get_table(bot, channel)
    table.upsert(data, keys)


def get_base_data(user):
    ''' Fetches "base" data according to user.
    Normally this is nick, ident, host and current time to be set to action_time in database.
    Ident and host might be missing when the full mask isn't provided,
    for example in handle_userKicked, where kickee doesn't get anything but name. '''

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
    ''' Handles all messages bot sees.
    If message is private message to bot, doesn't update.
    Otherwise updates the DB.
    - last_action = 'message'
    - last_message = message
    - message_time = current time '''

    # if user == channel -> this is a query -> don't update
    if user == channel:
        return

    data = get_base_data(user)
    data['last_action'] = 'message'
    data['last_message'] = message
    data['message_time'] = datetime.now()

    upsert_row(bot, channel, data)


def handle_userJoined(bot, user, channel):
    ''' Handles user joining the channel and auto-ops if op == True in database.
    - last_action = 'join' '''

    data = get_base_data(user)
    data['last_action'] = 'join'

    upsert_row(bot, channel, data)

    table = get_table(bot, channel)
    if table.find_one(nick=getNick(user), ident=getIdent(user), host=getHost(user), op=True):
        log.info('auto-opping %s' % user)
        bot.mode(channel, True, 'o', user=getNick(user))


def handle_userLeft(bot, user, channel, message):
    ''' Handles user leaving the channel (or quitting).
    For leaving, only updates the channel left.
    For quitting, updates all channels in network, which the user was on (as bot knows...)
    - last_action = 'left' '''

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
    ''' Handles user being kicked.
    As 'kickee' doesn't get full mask, it's only determined by nick.
    For kickee:
        - last_action = kicked by kicker [message]
    For kicker:
        - last_action = kicked kickee [message] '''

    data = get_base_data(kickee)
    data['last_action'] = 'kicked by %s [%s]' % (getNick(kicker), message)
    # We don't get full info from kickee, need to update by nick only
    upsert_row(bot, channel, data, ['nick'])

    # Update the kickers action also...
    data = get_base_data(kicker)
    data['last_action'] = 'kicked %s [%s]' % (getNick(kickee), message)
    upsert_row(bot, channel, data)


def handle_userRenamed(bot, user, newnick):
    ''' Handles nick change.
    Updates both data, related to old and new nick, doesn't remove anything from db.
    - last_action = nick change from oldnick to newnick '''

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
    ''' Handles action (/me etc). Ignores stuff directed to bot (/describe botnick etc).
    - last_action = action
    - last_message = message
    - message_time = current time '''

    # if action is directed to bot instead of channel -> don't log
    if channel == bot.nickname:
        return

    data = get_base_data(user)
    data['last_action'] = 'action'
    data['last_message'] = message
    data['message_time'] = datetime.now()

    upsert_row(bot, channel, data)


def command_add_op(bot, user, channel, args):
    ''' Adds op-status according to nickname or full hostmask. Only for admins.
    If user is found from database, set op = True and return info with full hostmask.
    Else returns user not found. '''

    if not isAdmin(user) or user == channel or not args:
        return

    table = get_table(bot, channel)

    # Get basedata for user to be opped
    u = get_base_data(args)

    # If we got full mask, use it..
    if 'nick' in u and 'ident' in u and 'host' in u:
        res = table.find_one(nick=u['nick'], ident=u['ident'], host=u['host'])
    # else use just nickname
    else:
        res = table.find_one(nick=u['nick'])

    if not res:
        return bot.say(channel, 'user not found')

    data = {'id': res['id'], 'op': True}
    table.upsert(data, ['id'])
    return bot.say(channel, 'auto-opping %s!%s@%s' % (res['nick'], res['ident'], res['host']))


def command_remove_op(bot, user, channel, args):
    ''' Removes op-status from nick. Logic same as command_add_op. Only for admins. '''

    if not isAdmin(user) or user == channel or not args:
        return

    table = get_table(bot, channel)

    # Get basedata for user to be opped
    u = get_base_data(args)

    # If we got full mask, use it..
    if 'nick' in u and 'ident' in u and 'host' in u:
        res = table.find_one(nick=u['nick'], ident=u['ident'], host=u['host'])
    # else use just nickname
    else:
        res = table.find_one(nick=u['nick'])

    if not res:
        return bot.say(channel, 'user not found')

    data = {'id': res['id'], 'op': False}
    table.upsert(data, ['id'])
    return bot.say(channel, 'removed auto-op from %s!%s@%s' % (res['nick'], res['ident'], res['host']))


def command_op(bot, user, channel, args):
    ''' Ops user if op = True for user or isAdmin. '''

    table = get_table(bot, channel)
    if table.find_one(nick=getNick(user), ident=getIdent(user), host=getHost(user), op=True) or isAdmin(user):
        log.info('opping %s on %s by request' % (user, channel))
        bot.mode(channel, True, 'o', user=getNick(user))


def command_list_ops(bot, user, channel, args):
    ''' Lists ops in current channel. Only for admins.
    By default lists nicks, if args == 'full', lists full hostmask. '''

    if not isAdmin(user) or user == channel:
        return

    table = get_table(bot, channel)
    if args.strip() == 'full':
        ops = ', '.join(['%s!%s@%s' % (r['nick'], r['ident'], r['host']) for r in table.find(op=True)])
    else:
        ops = ', '.join(['%s' % r['nick'] for r in table.find(op=True)])
    return bot.say(channel, 'ops: %s' % ops)


def __get_length_str(secs):
    days, hours, minutes, seconds = secs // 86400, secs // 3600, secs // 60 % 60, secs % 60

    if days > 0:
        return '%dd' % days
    if hours > 0:
        return '%dh' % hours
    if minutes > 0:
        return '%dm' % minutes
    if seconds > 0:
        return '%ds' % seconds
    return '0s'


def command_seen(bot, user, channel, args):
    '''Displays the last action by the given user'''
    if not args:
        return bot.say(channel, 'Please provide a nick to search...')

    table = get_table(bot, channel)

    # Return the first match, there shouldn't be multiples anyway
    user = table.find_one(nick=args)
    if not user:
        return bot.say(channel, "I haven't seen %s on %s" % (args, channel))

    # Calculate last seen in seconds
    last_seen = datetime.now() - user['action_time']
    # Get string for last seen
    last_seen = __get_length_str(last_seen.days * 86400 + last_seen.seconds)

    # If the last action was part or quit, show also the message
    if user['last_action'] in ['left', 'quit']:
        return bot.say(channel, "%s was last seen at %s (%s ago) [%s, %s]" %
                       (user['nick'],
                        '{0:%Y-%m-%d %H:%M:%S}'.format(user['action_time']),
                        last_seen,
                        user['last_action'],
                        user['last_message']
                        ))

    # Otherwise just show the time and action
    return bot.say(channel, "%s was last seen at %s (%s ago) [%s]" %
                   (user['nick'],
                    '{0:%Y-%m-%d %H:%M:%S}'.format(user['action_time']),
                    last_seen,
                    user['last_action']
                    ))
