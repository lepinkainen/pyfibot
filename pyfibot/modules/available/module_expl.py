# -*- encoding: utf-8 -*-

import os
import os.path
import sys
import re
import random
import fnmatch


def expl_parseterm(expl):
    expl = expl.split(" ")
    expl = expl[0]
    expl = expl.lower()
    expl = expl.strip()
    invalidchars = re.compile(r"[^a-z0-9\ :\.-]")
    expl = invalidchars.sub("_", expl)
    return expl


def expl_getdir(channel):
    expldir = os.path.join(sys.path[0], "expl", channel)
    if not os.path.exists(expldir):
        return None
    return expldir


def expl_getlist(expldir):
    list = os.listdir(expldir)
    dotfile = re.compile(r"(^[^\.])")
    list = filter(dotfile.match, list)
    return list


def expl_getexpl(expldir, term):
    f = file(os.path.join(expldir, term))
    expl = f.read()
    f.close()
    return expl


def check_params(bot, args, channel):
    """Do some initial checking for the stuff we need for every subcommand"""
    if not args:
        return False

    expldir = expl_getdir(channel)
    if not expldir:
        bot.log(
            "No expldir for channel %s, create %s to enable expl."
            % (channel, os.path.join(sys.path[0], "expl", channel))
        )
        return False

    termlist = expl_getlist(expldir)

    return expldir, termlist


def command_expl(bot, user, channel, args):
    """Explains terms. Usage: .expl <term> See also: .rexpl, .add, .del, .ls"""

    try:
        expldir, termlist = check_params(bot, args, channel)
    except TypeError:
        return

    term = expl_parseterm(args)
    if term in termlist:
        expl = expl_getexpl(expldir, term)
        return bot.say(channel, "'%s': %s" % (term, expl))
    else:
        return bot.say(channel, "Term '%s' not found. Try .help ls" % term)


def command_rexpl(bot, user, channel, args):
    """Returns random explanation. See also: .expl, .add, .del, .ls"""

    try:
        expldir, termlist = check_params(bot, "none", channel)
    except TypeError:
        return

    term = termlist[random.randrange(0, len(termlist) - 1)]
    expl = expl_getexpl(expldir, term)
    return bot.say(channel, "'%s': %s" % (term, expl))


def command_add(bot, user, channel, args):
    """Adds explanation for term. Usage: .add <term> <explanation> See also: .expl, .rexpl, .del, .ls"""

    try:
        expldir, termlist = check_params(bot, args, channel)
    except TypeError:
        bot.log("No expldir for channel %s" % channel)
        return

    args = args.split(" ", 1)
    if not args[1]:
        return bot.say(user, "No explanation given")

    term = expl_parseterm(args[0])
    if term in termlist:
        return bot.say(user, "Term '%s' already exists." % term)

    expl = args[1]
    f = file(os.path.join(expldir, term), "w")
    f.write(expl)
    f.write("\n")  # add a newline to make it easier to admin
    f.close()

    bot.log("Term '%s' for %s added by %s: %s" % (term, channel, user, term))
    return bot.say(user, "Term '%s' added: %s" % (term, expl))


def command_del(bot, user, channel, args):
    """Deletes term from explanation database. Usage: .del <term> See also: .expl, .rexpl, .add, .ls"""

    if not isAdmin(user):
        return

    try:
        expldir, termlist = check_params(bot, args, channel)
    except TypeError:
        return

    term = expl_parseterm(args)
    if term not in termlist:
        return bot.say(user, "Term '%s' doesn't exist." % term)

    expl = expl_getexpl(expldir, term)
    os.unlink(os.path.join(expldir, term))
    bot.log(
        "Term '%s' for %s deleted by %s (contained: %s)" % (term, channel, user, expl)
    )
    return bot.say(user, "Term '%s' deleted (contained: %s)" % (term, expl))


def command_ls(bot, user, channel, args):
    """Lists commands matching your Unix-like search query. Usage: .ls <query> Example: .ls ex[cp]la[!i]* matches 'explanation' and 'exclamation' but not 'explain'. See also: .expl, .rexpl, .add, .del"""

    try:
        expldir, termlist = check_params(bot, args, channel)
    except TypeError:
        return

    pattern = args.strip()
    matchlist = fnmatch.filter(termlist, pattern)
    matches = len(matchlist)

    if matches == 0:
        return bot.say(user, "No term matched '%s'." % pattern)
    first = ""
    if matches > 20:
        first = "first 20 of "

    matchlist.sort()
    return bot.say(
        user,
        "Terms matching '%s' (%stotal %d): %s"
        % (pattern, first, matches, ", ".join(matchlist[0:20])),
    )
