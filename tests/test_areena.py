# -*- coding: utf-8 -*-
from nose.tools import eq_
import bot_mock
from pyfibot.modules import module_urltitle
from utils import check_re


bot = bot_mock.BotMock()

lengh_str_regex = u'\d+(h|m|s)(\d+(m))?(\d+s)?'
views_str_regex = u'\d+(\.\d+)?(k|M|Billion|Trillion)?'
age_str_regex = u'(FRESH|(\d+(\.\d+)?(y|d) ago))'


def test_areena_radio():
    regex = u'Title: (.*?) \[%s - %s plays - %s( - exits in \d+ (weeks|days|hours|minutes))?\]' % (lengh_str_regex, views_str_regex, age_str_regex)
    msg = "http://areena.yle.fi/radio/2006973"
    module_urltitle.init(bot)
    check_re(regex, module_urltitle.handle_url(bot, None, "#channel", msg, msg)[1])


def test_areena_tv():
    regex = u'Title: (.*?) \[%s - %s plays - %s( - exits in \d+ (weeks|days|hours|minutes))?\]' % (lengh_str_regex, views_str_regex, age_str_regex)
    msg = "http://areena.yle.fi/tv/1999860"
    module_urltitle.init(bot)
    check_re(regex, module_urltitle.handle_url(bot, None, "#channel", msg, msg)[1])


def test_areena_series():
    regex = u'Title: (.*?) \[SERIES - \d+ episodes - latest episode: %s\]' % (age_str_regex)
    msg = "http://areena.yle.fi/tv/2129619"
    module_urltitle.init(bot)
    check_re(regex, module_urltitle.handle_url(bot, None, "#channel", msg, msg)[1])


def test_areena_live():
    msg = "http://areena.yle.fi/tv/suora/tv2"
    module_urltitle.init(bot)
    eq_(('#channel', u'Title: Yle TV2 (LIVE)'), module_urltitle.handle_url(bot, None, "#channel", msg, msg))
