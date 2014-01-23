from __future__ import unicode_literals, print_function, division
import subprocess
import sys

import logging
log = logging.getLogger("update")


def command_update(bot, user, channel, args):
    """Update bot sources from git"""
    if not isAdmin(user):
        return

    pull_ok = False
    pip_ok = False

    cmd = ['git', 'pull']
    cwd = sys.path[0]

    log.debug("Executing git pull in %s" % cwd)

    p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res = p.wait()
    out, err = p.communicate()

    if res:
        bot.say(channel, "Git pull failed:")
        for line in out.split("\n"):
            bot.say(channel, "%s" % line)
    else:
        pull_ok = True
        bot.say(channel, "Git update OK:")
        for line in out.split("\n"):
            bot.say(channel, "%s" % line)

    # only report errors when the update failed, git uses stderr for normal output..
    if res and err:
        bot.say(channel, "Errors: %s" % err)

    # fetch new required packages if needed
    cmd = ['../bin/pip', 'install', '-r', '../requirements.txt']
    log.debug("executing pip install in %s" % cwd)

    p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res = p.wait()
    out, err = p.communicate()

    if res:
        bot.say(channel, "Update failed:")
        for line in out.split("\n"):
            bot.say(channel, "%s" % line)
    else:
        bot.say(channel, "Package status OK")
        pip_ok = True

    # Rehash after successful update
    if pip_ok and pull_ok:
        bot.command_rehash(user, channel, args)
