from __future__ import unicode_literals, print_function, division
import subprocess
import sys

import logging
log = logging.getLogger("update")


def command_update(bot, user, channel, args):
    """Update bot sources from git"""
    if not isAdmin(user):
        return

    cmd = ['git', 'pull']
    cwd = sys.path[0]

    log.debug("Executing git pull in %s" % cwd)

    p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res = p.wait()
    out, err = p.communicate()

    if res:
        bot.say(channel, "Update failed: %s" % out)
    else:
        bot.say(channel, "Update done: %s" % out)
    if err:
        bot.say(channel, "Errors: %s" % err)
