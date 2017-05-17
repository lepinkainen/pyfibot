# -*- coding: utf-8 -*-
"""
    Example of admin only commands
"""

from __future__ import unicode_literals, print_function, division


def admin_allow(bot, user, channel, args):
    bot.say(channel, "Example of a command only allowed to an admin")
