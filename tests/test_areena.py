# -*- coding: utf-8 -*-

import bot_mock
from pyfibot.modules import module_urltitle

from utils import check_re
import pytest

from vcr import VCR
my_vcr = VCR(path_transformer=VCR.ensure_suffix('.yaml'),
             cassette_library_dir="tests/cassettes/",
             record_mode=pytest.config.getoption("--vcrmode"))


@pytest.fixture
def botmock():
    bot = bot_mock.BotMock()
    module_urltitle.init(bot)
    return bot

lengh_str_regex = u'\d+(h|m|s)(\d+(m))?(\d+s)?'
views_str_regex = u'\d+(\.\d+)?(k|M|Billion|Trillion)?'
age_str_regex = u'(FRESH|(\d+(\.\d+)?(y|d) ago))'


@my_vcr.use_cassette
def test_areena_radio(botmock):
    regex = u'Title: (.*?) \[%s - %s plays - %s( - exits in \d+ (weeks|days|hours|minutes))?\]' % (lengh_str_regex, views_str_regex, age_str_regex)
    msg = "http://areena.yle.fi/1-2006973"
    check_re(regex, module_urltitle.handle_url(botmock, None, "#channel", msg, msg)[1])


@my_vcr.use_cassette
def test_areena_tv(botmock):
    regex = u'Title: (.*?) \[%s - %s plays - %s( - exits in \d+ (weeks|days|hours|minutes))?\]' % (lengh_str_regex, views_str_regex, age_str_regex)
    msg = "http://areena.yle.fi/1-3210197"
    check_re(regex, module_urltitle.handle_url(botmock, None, "#channel", msg, msg)[1])


@my_vcr.use_cassette
def test_areena_series(botmock):
    regex = u'Title: (.*?) \[SERIES - \d+ episodes - latest episode: %s\]' % (age_str_regex)
    msg = "http://areena.yle.fi/1-2540167"
    check_re(regex, module_urltitle.handle_url(botmock, None, "#channel", msg, msg)[1])


@my_vcr.use_cassette
def test_areena_live(botmock):
    regex = u'Title: Yle TV2 - (.*?)( <http://areena.yle.fi/\d-\d+>)? \(LIVE\)'
    msg = "http://areena.yle.fi/tv/suora/tv2"
    check_re(regex, module_urltitle.handle_url(botmock, None, "#channel", msg, msg)[1])
