# -*- coding: utf-8 -*-
"""
Commands:
.autoop add channel nick!ident@example.org         adds hostmask to channels auto-op list
.autoop remove channel nick!ident@example.org      removes hostmask from channels auto-op list
.autoop list <channel>                             lists ops in current channel or channel
.autoop status                                      lists channels where user is op
.op
"""

from __future__ import unicode_literals, print_function, division
import sqlite3
import re


COMMANDS = ["add", "remove", "list", "status"]
CHANNEL_PREFIXES = "&#!+"


def init(botconfig):
    open_db(True)


def open_db(createTable=False):
    conn = sqlite3.connect("module_autoop.db")
    c = conn.cursor()
    if createTable:
        c.execute("CREATE TABLE IF NOT EXISTS autoops (channel, hostmask, modes);")
        conn.commit()
    return conn, c


def add_op(channel, hostmask, modes="o"):
    if not get_op_status(channel, hostmask):
        conn, c = open_db()
        c.execute("INSERT INTO autoops VALUES (?, ?, ?);", (channel, hostmask, modes))
        conn.commit()
        conn.close()
        return True


def remove_op(channel, hostmask):
    if get_op_status(channel, hostmask):
        conn, c = open_db()
        c.execute(
            "DELETE FROM autoops WHERE channel = ? AND ? GLOB hostmask;",
            (channel, hostmask),
        )
        conn.commit()
        conn.close()
        return True


def get_op_status(channel, hostmask):
    conn, c = open_db()
    c.execute(
        "SELECT * FROM autoops WHERE channel = ? AND ? GLOB hostmask LIMIT 1;",
        (channel, hostmask),
    )
    if c.fetchone():
        retval = True
    else:
        retval = False
    conn.close()
    return retval


def get_user_channels(hostmask):
    conn, c = open_db()
    c.execute("SELECT channel FROM autoops WHERE ? GLOB hostmask;", (hostmask,))
    rows = c.fetchall()
    conn.close()
    return rows


def get_ops(channel):
    conn, c = open_db()
    c.execute("SELECT hostmask FROM autoops WHERE channel = ?;", (channel,))
    rows = c.fetchall()
    conn.close()
    return rows


def check_hostmask(hostmask):
    rg = re.compile(
        ".*?(!).*?(@).*?", re.IGNORECASE | re.DOTALL
    )  # regex for checking hostmask format
    if re.match(rg, hostmask):
        return True
    return False


def op_user(bot, user, channel):
    nick = bot.getNick(user)
    bot.log("auto-opping %s on %s" % (user, channel))
    bot.mode(channel, True, "o", user=nick)


def handle_userJoined(bot, user, channel):
    if bot.isAdmin(user) or get_op_status(channel, user):
        op_user(bot, user, channel)


def command_autoop(bot, user, channel, args):
    """Usage: .autoop [add|remove|list|status]"""

    if not args:
        return bot.say(channel, "Valid commands are %s" % ", ".join(map(str, COMMANDS)))

    args = args.split()
    command = args[0]
    if command not in COMMANDS:
        return bot.say(
            channel,
            "Invalid command, valid commands are %s" % ", ".join(map(str, COMMANDS)),
        )

    if command == "list":
        if len(args) > 1:
            list_channel = args[1]
        else:
            list_channel = channel
        if list_channel[0] not in CHANNEL_PREFIXES:
            return bot.say(
                channel, 'Channel name must start with one of "%s"' % CHANNEL_PREFIXES
            )

        ops = get_ops(list_channel)
        if ops:
            return bot.say(
                channel,
                "%s ops: %s" % (list_channel, ", ".join(str(i[0]) for i in ops)),
            )
        return bot.say(channel, "%s doesn't have any ops." % list_channel)

    elif command == "status":
        if channel[0] not in CHANNEL_PREFIXES:
            channel_list = get_user_channels(user)
            if channel_list:
                return bot.say(
                    channel,
                    "You're auto-opped on %s"
                    % ", ".join(str(i[0]) for i in channel_list),
                )
            return bot.say(channel, "You're not auto-opped on any channel.")
        else:
            if get_op_status(channel, user):
                return bot.say(channel, "You're op in %s." % channel)
            return bot.say(channel, "You're not an op in %s." % channel)

    else:
        if bot.isAdmin(user):
            if len(args) < 3:
                return bot.say(
                    channel, "Command must have channel and hostmask as arguments."
                )

            if not (args[1][0] in CHANNEL_PREFIXES and check_hostmask(args[2])):
                return bot.say(
                    channel,
                    'Channel name must start with one of "%s" and hostmask must be in format nick!ident@hostma.sk'
                    % CHANNEL_PREFIXES,
                )

            if command == "add":
                if add_op(args[1], args[2]):
                    return bot.say(channel, "OP added.")
                return bot.say(channel, "Adding OP failed, is user already auto-opped?")
            elif command == "remove":
                if remove_op(args[1], args[2]):
                    return bot.say(channel, "OP removed.")
                return bot.say(
                    channel, "Removing OP failed, is user the user auto-opped?"
                )
        else:
            return bot.say(channel, "You must be bot admin to use this feature.")


def command_op(bot, user, channel, args):
    """Get op status from bot if you are authorized"""
    if bot.isAdmin(user) or get_op_status(channel, user):
        op_user(bot, user, channel)
