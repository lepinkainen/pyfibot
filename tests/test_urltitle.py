# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from nose.tools import eq_, ok_
import bot_mock
from pyfibot.modules import module_urltitle
from utils import check_re


bot = bot_mock.BotMock()

lengh_str_regex = '\d+(h|m|s)(\d+(m))?(\d+s)?'
views_str_regex = '\d+(\.\d+)?(k|M|Billion|Trillion)?'
age_str_regex = '(FRESH|(\d+(\.\d+)?(y|d) ago))'


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
    eq_(("#channel", "Title: Saksassa syntyi jättivauva - yli kuusi kiloa!"), module_urltitle.handle_url(bot, None, "#channel", msg, msg))


def test_iltasanomat():
    msg = "http://www.iltasanomat.fi/viihde/art-1288596309269.html"
    module_urltitle.init(bot)
    eq_(("#channel", "Title: Muistatko Mari Sainion juontaman sarjan, josta sai palkinnoksi isdn-liittymän?"), module_urltitle.handle_url(bot, None, "#channel", msg, msg))


def test_verkkokauppacom():
    msg = "http://www.verkkokauppa.com/fi/product/34214/dkqht/Sony-NEX-3N-mikrojarjestelmakamera-16-50-mm-objektiivi-musta"
    module_urltitle.init(bot)
    regex = 'Title: Sony NEX-3N mikrojärjestelmäkamera \+ 16-50 mm objektiivi, musta \| \d+,\d+ € \(.*?\)'
    check_re(regex, module_urltitle.handle_url(bot, None, "#channel", msg, msg)[1])


def test_stackoverflow():
    msg = "http://stackoverflow.com/questions/6905508/python-search-html-document-for-capital-letters"
    module_urltitle.init(bot)
    eq_(("#channel", "Title: Python search HTML document for capital letters - 0pts - python/regex/coda/letters/capitalize"), module_urltitle.handle_url(bot, None, "#channel", msg, msg))


def test_wiki_fi():
    msg = "http://fi.wikipedia.org/wiki/Kimi_Räikkönen"
    module_urltitle.init(bot)
    eq_(("#channel", "Title: Kimi-Matias Räikkönen on suomalainen autourheilija ja Formula 1:n maailmanmestari."), module_urltitle.handle_url(bot, None, "#channel", msg, msg))


def test_wiki_en():
    msg = "http://en.wikipedia.org/wiki/IPhone"
    module_urltitle.init(bot)
    eq_(("#channel", "Title: iPhone is a line of smartphones designed and marketed by Apple Inc."), module_urltitle.handle_url(bot, None, "#channel", msg, msg))


def test_imdb():
    regex = 'Title: Wreck-It Ralph \(2012\) - [\d.]{1,}/10 \(%s votes\) - .*' % views_str_regex
    msg = "http://www.imdb.com/title/tt1772341/"
    module_urltitle.init(bot)
    check_re(regex, module_urltitle.handle_url(bot, None, "#channel", msg, msg)[1])


def test_youtube():
    regex = 'Title: (.*?) by (.*?) \[%s - \[\** *\] - %s views - %s( - XXX)?\]' % (lengh_str_regex, views_str_regex, age_str_regex)
    msg = "http://www.youtube.com/watch?v=awsolTK175c"
    module_urltitle.init(bot)
    check_re(regex, module_urltitle.handle_url(bot, None, "#channel", msg, msg)[1])


def test_vimeo():
    regex = 'Title: (.*?) by (.*?) \[%s - %s likes - %s views - %s]' % (lengh_str_regex, views_str_regex, views_str_regex, age_str_regex)
    msg = 'http://vimeo.com/29996808'
    module_urltitle.init(bot)
    check_re(regex, module_urltitle.handle_url(bot, None, "#channel", msg, msg)[1])


def test_liveleak():
    regex = 'Title: (.*?) by (.*?) \[%s views - Jul-23-2013 - tags\: sword, cut, hand, watermelon, fail\]' % (views_str_regex)
    msg = 'http://www.liveleak.com/view?i=f8e_1374614129'
    module_urltitle.init(bot)
    check_re(regex, module_urltitle.handle_url(bot, None, "#channel", msg, msg)[1])


def test_ebay():
    msg = 'https://ebay.com/itm/390629338875'
    regex = 'Title: .*? \[\d+\.\de \(postage \d+\.\de\) - over \d+ available - ships from .*?\]'
    module_urltitle.init(bot)
    check_re(regex, module_urltitle.handle_url(bot, None, "#channel", msg, msg)[1])


def test_ebay_cgi():
    msg = 'http://cgi.ebay.co.uk/ws/eBayISAPI.dll?ViewItem&item=121136837564'
    regex = 'Title: .*? \[\d+\.\de - over \d+ available - ships from .*?\]'
    module_urltitle.init(bot)
    check_re(regex, module_urltitle.handle_url(bot, None, "#channel", msg, msg)[1])


def test_dx():
    regex = 'Title: Wireless Bluetooth Audio Music Receiver Adapter - Black \[\d+\.\d+e - \[\** *\] - \d+ reviews\]'
    msg = 'http://dx.com/p/wireless-bluetooth-audio-music-receiver-adapter-black-151659'
    module_urltitle.init(bot)
    check_re(regex, module_urltitle.handle_url(bot, None, "#channel", msg, msg)[1])


def test_alko():
    regex = 'Title: Sandels IV A tölkki \[\d\.\d\de, \d\.\d\dl, \d\.\d\%\, \d\.\d\de/l, \d\.\d\de/annos, oluet]'
    msg = 'http://www.alko.fi/tuotteet/798684/'
    module_urltitle.init(bot)
    check_re(regex, module_urltitle.handle_url(bot, None, "#channel", msg, msg)[1])


def test_google_play_music():
    msg = 'https://play.google.com/music/m/Tkyqfh5koeirtbi76b2tsee6e2y'
    module_urltitle.init(bot)
    responses = [('#channel', 'Title: Villiviini - Ultra Bra'), None]
    ok_(module_urltitle.handle_url(bot, None, "#channel", msg, msg) in responses)


def test_poliisi():
    msg = 'http://www.poliisi.fi/poliisi/lappi14/home.nsf/PFBD/76D41E0F8B4A85E5C2257C760045DAC6'
    title = 'Title: Poliisi kaipaa ajoneuvoyhdistelmää kolaroinutta henkilöä'
    module_urltitle.init(bot)
    eq_(title, module_urltitle.handle_url(bot, None, "#channel", msg, msg)[1])
