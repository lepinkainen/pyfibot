# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from nose.tools import eq_
import bot_mock
from pyfibot.modules.module_rss import init, finalize, command_rss, Feed
from utils import check_re

ADMIN_USER = 'example!example@example.com'
bot = None


def setup_module():
    global bot
    factory = bot_mock.FactoryMock(config={'admins': [ADMIN_USER]})
    init(factory, testing=True)
    bot = factory.find_bot_for_network('nerv')


def teardown_module():
    finalize()


def test_init():
    eq_(('#pyfibot', 'feed added with 50 items'), command_rss(bot, ADMIN_USER, '#pyfibot', 'add ./tests/static/test_rss_init.xml'))
    eq_(
        ('#pyfibot', '[Uutiset - Ampparit] Tuuli riepotteli Rosbergiakin (Yle) <http://www.ampparit.com/redir.php?id=237104024>'),
        command_rss(bot, ADMIN_USER, '#pyfibot', 'latest 1')
    )


def test_update():
    global f
    f = Feed('nerv', '#pyfibot', url=r'./tests/static/test_rss_init.xml')
    f.update_feed_info({'url': r'./tests/static/test_rss_check.xml'})
    eq_(
        None,
        command_rss(bot, ADMIN_USER, '#pyfibot', 'update 1')
    )


def test_command_latest():
    eq_(
        ('#pyfibot', '[Uutiset - Ampparit] Turun Ruisrock käynnistyi aurinkoisessa säässä (Karjalainen) <http://www.ampparit.com/redir.php?id=1198870394>'),
        command_rss(bot, ADMIN_USER, '#pyfibot', 'latest 1')
    )


def test_add_feed():
    check_re(
        r'feed added with \d+ items',
        command_rss(bot, ADMIN_USER, '#pyfibot', 'add http://feeds.feedburner.com/ampparit-kaikki?format=xml')[1]
    )


def test_command():
    eq_(bot.say('#pyfibot', 'rss: valid arguments are [list, add, remove, latest, update]'), command_rss(bot, 'pyfibot!pyfibot@example.com', '#pyfibot', ''))


def test_command_list():
    eq_(None, command_rss(bot, ADMIN_USER, '#pyfibot', 'list'))


def test_command_remove():
    eq_(
        ('#pyfibot', 'only "latest" and "list" available for non-admins'),
        command_rss(bot, 'pyfibot!pyfibot@example.example.com', '#pyfibot', 'remove')
    )


def test_command_remove_2():
    eq_(
        ('#pyfibot', 'syntax: ".rss remove <id from list>"'),
        command_rss(bot, ADMIN_USER, '#pyfibot', 'remove')
    )


def test_command_remove_3():
    eq_(
        ('#pyfibot', 'feed not found, no action taken'),
        command_rss(bot, ADMIN_USER, '#pyfibot', 'remove 123')
    )


def test_command_remove_4():
    eq_(
        ('#pyfibot', 'feed "Uutiset - Ampparit.com" <./tests/static/test_rss_check.xml> removed'),
        command_rss(bot, ADMIN_USER, '#pyfibot', 'remove 1')
    )


def test_command_add():
    check_re(
        r'feed added with \d+ items',
        command_rss(bot, ADMIN_USER, '#pyfibot', 'add ./tests/static/test_rss_init.xml')[1]
    )


def test_command_add_2():
    eq_(
        ('#pyfibot', 'feed already added'),
        command_rss(bot, ADMIN_USER, '#pyfibot', 'add ./tests/static/test_rss_init.xml')
    )
