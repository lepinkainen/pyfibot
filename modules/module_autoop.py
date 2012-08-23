"""
$Id$
$HeadURL$

Commands:
.autoop add/del/status/list
.op

Nick-format: nick!ident@example.org

Supports adding/deleting multiple autoop-rules:
.autoop add #testchannel firstNick!ident@example.org secNick!ident@example.org

In add/del #channel needed, if changes done in query. If changes are made in #channel, defaults to current #channel.

config-file in root/modules/module_autooop.conf
config-format:
 'nick!ident@example.org':
 - '#channelOne'
 - '#channelTwo'

 'secNick!ident@example.org':
 - '#channelTwo'
"""

import fnmatch
import yaml
import os.path
import sys
import re

oplistfile = os.path.join(sys.path[0], 'modules', 'module_autoop.conf')
oplist = dict()


def init(botconfig):
    global oplist
    if os.path.exists(oplistfile):
        oplist = yaml.load(file(oplistfile))


def writeConfig():
    # open file for writing (note, removes all markings that have been made to config-file prior to .rehash
    f = open(oplistfile, 'w')
    yaml.dump(oplist, f, default_flow_style=False)
    f.close()


def isAutoOppable(user, channel):
    for pattern in oplist:
        if fnmatch.fnmatch(user, pattern):
            if channel in oplist[pattern]:
                return True


def handle_userJoined(bot, user, channel):
    if isAdmin(user) or isAutoOppable(user, channel):
        nick = getNick(user)
        bot.log('auto-opping %s on %s' % (user, channel))
        bot.mode(channel, True, 'o', user=nick)


def handle_args(args, channel):
    message = ''
    nicks = list()
    rg = re.compile('.*?(!).*?(@).*?', re.IGNORECASE | re.DOTALL)    # regex for validating nick format
    if re.match(rg, args[0].strip()) is None and args[0].strip()[0] == '#':
        op_channel = args[0].strip()
        for nick in args[1:]:
            if re.match(rg, nick):
                nicks.append(nick)
            else:
                message += '%s not in correct format. ' % nick
    else:
        op_channel = channel
        for nick in args[0:]:
            if re.match(rg, nick):
                nicks.append(nick)
            else:
                message += '%s not in correct format. ' % nick
    return nicks, op_channel, message


def autoop_status(user, channel, args):
    nick = getNick(user)
    if isAdmin(user):
        return '%s: you are %s on %s, status: bot admin' % (nick, user, channel)
    elif isAutoOppable(user, channel):
        return '%s: you are %s on %s, status: auto-op' % (nick, user, channel)
    else:
        return '%s: you are %s on %s: status: -' % (nick, user, channel)


def autoop_add(user, channel, args):
    if isAdmin(user):
        nicks = list()
        message = ''
        if len(args) > 0:
            nicks, op_channel, message = handle_args(args, channel)
            if cmp(op_channel, user) != 0:
                for nick in nicks:
                    if nick in oplist:    # if already in oplist, just add to existing list
                        if op_channel in oplist[nick]:    # if not in nicks channel list, add
                            message += 'Auto-op for %s already in %s. ' % (nick, op_channel)
                        else:
                            message += 'Auto-op for %s in %s added. ' % (nick, op_channel)
                            oplist[nick].append(op_channel)
                    else:
                        message += 'Auto-op for %s in %s added. ' % (nick, op_channel)
                        oplist[nick] = list()
                        oplist[nick].append(op_channel)
                writeConfig()
            else:
                message = '#channel always needed when making changes in query!'
            return message
        else:
            return 'Usage: .autoop add [#channel] nick!ident@hostma.sk'


def autoop_del(user, channel, args):
    if isAdmin(user):
        message = ''
        if len(args) > 0:
            nicks, op_channel, message = handle_args(args, channel)
            if cmp(op_channel, user) != 0:
                for nick in nicks:
                    if nick in oplist:
                        if op_channel in oplist[nick]:  # if in nicks channel list, remove
                            message += 'Auto-op for %s in %s removed. ' % (nick, op_channel)
                            oplist[nick].remove(op_channel)
                            if len(oplist[nick]) == 0:
                                del oplist[nick]
                        else:
                            message += 'No auto-op for %s in %s. ' % (nick, op_channel)
                    else:
                        message += 'No auto-op for %s in %s. ' % (nick, op_channel)
                writeConfig()
            else:
                message = '#channel always needed when making changes in query!'
            return message
        else:
            return 'Usage: .autoop del [#channel] nick!ident@hostma.sk'


def autoop_list(user, channel, args):
    if isAdmin(user):
        i = 0
        rg = re.compile('.*?(!).*?(@).*?', re.IGNORECASE | re.DOTALL)  # regex for validating nick format
        if (len(args) == 0 or (re.match(rg, args[0].strip()) is None and args[0].strip()[0] == '#')) and args[0] != 'me':
            if len(args) == 0:
                op_channel = channel
            elif re.match(rg, args[0].strip()) is None and args[0].strip()[0] == '#':
                op_channel = args[0].strip()
            message = 'Auto-ops in %s: ' % op_channel
            for nick, channels in oplist.items():
                for chan in channels:
                    if chan == op_channel:
                        message += nick + ' '
                        i = i + 1
            if i != 0:
                return message
            else:
                return '%s has no auto-ops.' % op_channel
        elif re.match(rg, args[0].strip()) or args[0] == 'me':
            if args[0] != 'me':
                nick = args[0].strip()
            else:
                nick = user
            message = '%s auto-op in: ' % nick
            if nick in oplist:
                for chan in oplist[nick]:
                    message += chan + ' '
                    i = i + 1
            if i != 0:
                return message
            else:
                return '%s not auto-op anywhere.' % nick
        else:
            return 'Usage: .autoop_list [#channel _or_ nick!ident@hostma.sk]'
    else:
        nick = user
        i = 0
        message = '%s auto-op in: ' % nick
        if nick in oplist:
            for chan in oplist[nick]:
                message += chan + ' '
                i = i + 1
        if i != 0:
            return message
        else:
            return '%s not auto-op anywhere.' % nick


def make_valid_commands_msg(commands):
    message = 'Valid commands are: '
    for command in commands:
        message += command
        message += ', '
    message = message[:-2]
    message += '.'
    return message


def command_op(bot, user, channel, args):
    if isAdmin(user) or isAutoOppable(user, channel):
        nick = getNick(user)
        bot.log('opping %s by request on %s' % (user, channel))
        bot.mode(channel, True, 'o', user=nick)


def command_autoop(bot, user, channel, args):
    commands = {'add': autoop_add, 'del': autoop_del, 'list': autoop_list, 'status': autoop_status}
    args = args.split()
    if len(args) > 0:
        command = args[0]
        if command in commands:
            args.remove(command)
            message = commands[command](user, channel, args)
        else:
            message = make_valid_commands_msg(commands)
    else:
        message = make_valid_commands_msg(commands)
    return bot.say(channel, message)
