# -*- coding: utf-8 -*-
from nose.tools import eq_
import bot_mock
from pyfibot.modules import module_urltitle

bot = bot_mock.BotMock()


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
