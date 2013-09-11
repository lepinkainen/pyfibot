# -*- coding: utf-8 -*-
from nose.tools import eq_
import bot_mock
from pyfibot.modules import module_urltitle
from utils import check_re


bot = bot_mock.BotMock()

lengh_str_regex = '\d+(h|m|s)(\d+(m))?(\d+s)?'
views_str_regex = '\d+(\.\d+)?(k|M|Billion|Trillion)? views'
age_str_regex = '(FRESH|(\d+(\.\d+)?(y|d) ago))'


def test_imdb_ignore():
    msg = "http://www.imdb.com/title/tt1772341/"
    module_urltitle.init(bot)
    eq_(None, module_urltitle.handle_url(bot, None, "#channel", msg, msg))


def test_spotify_ignore():
    msg = "http://open.spotify.com/artist/4tuiQRw9bC9HZhSFJEJ9Mz"
    module_urltitle.init(bot)
    eq_(None, module_urltitle.handle_url(bot, None, "#channel", msg, msg))


def test_manual_ignore():
    msg = "- foofoo http://www.youtube.com/"
    module_urltitle.init(bot)
    eq_(None, module_urltitle.handle_url(bot, None, "#channel", msg, msg))


def test_iltalehti():
    msg = "http://www.iltalehti.fi/ulkomaat/2013072917307393_ul.shtml"
    module_urltitle.init(bot)
    eq_(("#channel", u"Title: Saksassa syntyi jättivauva - yli kuusi kiloa!"), module_urltitle.handle_url(bot, None, "#channel", msg, msg))


def test_iltasanomat():
    msg = "http://www.iltasanomat.fi/viihde/art-1288596309269.html"
    module_urltitle.init(bot)
    eq_(("#channel", u"Title: Muistatko Mari Sainion juontaman sarjan, josta sai palkinnoksi isdn-liittymän?"), module_urltitle.handle_url(bot, None, "#channel", msg, msg))


def test_verkkokauppacom():
    msg = "http://www.verkkokauppa.com/fi/product/34214/dkqht/Sony-NEX-3N-mikrojarjestelmakamera-16-50-mm-objektiivi-musta"
    module_urltitle.init(bot)
    eq_(("#channel", u"Title: Sony NEX-3N mikrojärjestelmäkamera + 16-50 mm objektiivi, musta. | 399,90 € (heti)"), module_urltitle.handle_url(bot, None, "#channel", msg, msg))


def test_stackoverflow():
    msg = "http://stackoverflow.com/questions/6905508/python-search-html-document-for-capital-letters"
    module_urltitle.init(bot)
    eq_(("#channel", u"Title: Python search HTML document for capital letters - 0pts - python/regex/coda/letters/capitalize"), module_urltitle.handle_url(bot, None, "#channel", msg, msg))


def test_wiki_fi():
    msg = "http://fi.wikipedia.org/wiki/Kimi_Räikkönen"
    module_urltitle.init(bot)
    eq_(("#channel", u"Title: Kimi-Matias Räikkönen on suomalainen autourheilija ja Formula 1:n maailmanmestari."), module_urltitle.handle_url(bot, None, "#channel", msg, msg))


def test_wiki_en():
    msg = "http://en.wikipedia.org/wiki/IPhone"
    module_urltitle.init(bot)
    eq_(("#channel", u"Title: The iPhone is a line of smartphones designed and marketed by Apple Inc."), module_urltitle.handle_url(bot, None, "#channel", msg, msg))


def test_areena_radio():
    regex = 'Title: (.*?) \[\d+ min - \d+ plays - %s( - exits in \d+ (weeks|days|hours|minutes))?\]' % (age_str_regex)
    msg = "http://areena.yle.fi/radio/2006973"
    module_urltitle.init(bot)
    assert check_re(regex, module_urltitle.handle_url(bot, None, "#channel", msg, msg)[1])


def test_areena_tv():
    regex = 'Title: (.*?) \[\d+ min - \d+ plays - %s( - exits in \d+ (weeks|days|hours|minutes))?\]' % (age_str_regex)
    msg = "http://areena.yle.fi/tv/1999860"
    module_urltitle.init(bot)
    assert check_re(regex, module_urltitle.handle_url(bot, None, "#channel", msg, msg)[1])


def test_areena_series():
    regex = 'Title: (.*?) \[SERIES - \d+ episodes - latest episode: %s\]' % (age_str_regex)
    msg = "http://areena.yle.fi/tv/serranonperhe"
    module_urltitle.init(bot)
    assert check_re(regex, module_urltitle.handle_url(bot, None, "#channel", msg, msg)[1])


def test_youtube():
    regex = 'Title: (.*?) by (.*?) \[%s - \[\**\] - %s - %s( - XXX)?\]' % (lengh_str_regex, views_str_regex, age_str_regex)
    msg = "http://www.youtube.com/watch?v=awsolTK175c"
    module_urltitle.init(bot)
    assert check_re(regex, module_urltitle.handle_url(bot, None, "#channel", msg, msg)[1])


def test_vimeo():
    regex = 'Title: (.*?) by (.*?) \[%s - \d+ likes - %s - %s]' % (lengh_str_regex, views_str_regex, age_str_regex)
    msg = 'http://vimeo.com/29996808'
    module_urltitle.init(bot)
    assert check_re(regex, module_urltitle.handle_url(bot, None, "#channel", msg, msg)[1])


def test_liveleak():
    regex = 'Title: (.*?) by (.*?) \[%s - Jul-23-2013 - tags\: sword, cut, hand, watermelon, fail\]' % (views_str_regex)
    msg = 'http://www.liveleak.com/view?i=f8e_1374614129'
    module_urltitle.init(bot)
    assert check_re(regex, module_urltitle.handle_url(bot, None, "#channel", msg, msg)[1])
