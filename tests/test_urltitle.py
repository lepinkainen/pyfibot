# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from nose.tools import eq_, ok_
import bot_mock
from pyfibot.modules import module_urltitle
from utils import check_re
from time import sleep

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


lengh_str_regex = '\d+(h|m|s)(\d+(m))?(\d+s)?'
views_str_regex = '\d+(\.\d+)?(k|M|Billion|Trillion)?'
age_str_regex = '(FRESH|(\d+(\.\d+)?(y|d) ago))'


@my_vcr.use_cassette
def test_spotify_ignore(botmock):
    msg = "http://open.spotify.com/artist/4tuiQRw9bC9HZhSFJEJ9Mz"
    eq_(None, module_urltitle.handle_url(botmock, None, "#channel", msg, msg))


@my_vcr.use_cassette
def test_manual_ignore(botmock):
    msg = "- foofoo http://www.youtube.com/"
    eq_(None, module_urltitle.handle_url(botmock, None, "#channel", msg, msg))


@my_vcr.use_cassette
def test_iltalehti(botmock):
    msg = "http://www.iltalehti.fi/ulkomaat/2013072917307393_ul.shtml"
    eq_(("#channel", "Title: Saksassa syntyi jättivauva - yli kuusi kiloa!"), module_urltitle.handle_url(botmock, None, "#channel", msg, msg))


@my_vcr.use_cassette
def test_iltasanomat(botmock):
    msg = "http://www.iltasanomat.fi/viihde/art-1288596309269.html"
    eq_(("#channel", "Title: Muistatko Mari Sainion juontaman sarjan, josta sai palkinnoksi isdn-liittymän?"), module_urltitle.handle_url(botmock, None, "#channel", msg, msg))


@my_vcr.use_cassette
def test_verkkokauppacom(botmock):
    msg = "http://www.verkkokauppa.com/fi/product/55124/dfbfn/Coca-Cola-Vanilla-USA-virvoitusjuoma-355-ml"
    regex = 'Title: Coca-Cola Vanilla USA virvoitusjuoma 355 ml \| \d+,\d+ € \(.*?\)'
    check_re(regex, module_urltitle.handle_url(botmock, None, "#channel", msg, msg)[1])


@my_vcr.use_cassette
def test_stackoverflow(botmock):
    msg = "http://stackoverflow.com/questions/6905508/python-search-html-document-for-capital-letters"
    eq_(("#channel", "Title: Python search HTML document for capital letters - 0pts - python/regex/coda/letters/capitalize"), module_urltitle.handle_url(botmock, None, "#channel", msg, msg))


@my_vcr.use_cassette
def test_wiki_fi(botmock):
    msg = "http://fi.wikipedia.org/wiki/Kimi_Räikkönen"
    eq_(("#channel", "Title: Kimi-Matias Räikkönen on suomalainen autourheilija ja Formula 1:n maailmanmestari."), module_urltitle.handle_url(botmock, None, "#channel", msg, msg))


@my_vcr.use_cassette
def test_wiki_en(botmock):
    msg = "http://en.wikipedia.org/wiki/IPhone"
    eq_(("#channel", "Title: iPhone is a line of smartphones designed and marketed by Apple Inc."), module_urltitle.handle_url(botmock, None, "#channel", msg, msg))


@my_vcr.use_cassette
def test_imdb(botmock):
    regex = 'Title: Wreck-It Ralph \(2012\) - [\d.]{1,}/10 \(%s votes\) - .*' % views_str_regex
    msg = "http://www.imdb.com/title/tt1772341/"
    check_re(regex, module_urltitle.handle_url(botmock, None, "#channel", msg, msg)[1])


# def test_youtube(botmock):
#     regex = 'Title: (.*?) by (.*?) \[%s - %s views - %s( - age restricted)?\]' % (lengh_str_regex, views_str_regex, age_str_regex)
#     msg = "http://www.youtube.com/watch?v=awsolTK175c"
#     module_urltitle.init(botmock)
#     check_re(regex, module_urltitle.handle_url(botmock, None, "#channel", msg, msg)[1])


@my_vcr.use_cassette
def test_vimeo(botmock):
    regex = 'Title: (.*?) by (.*?) \[%s - %s likes - %s views - %s]' % (lengh_str_regex, views_str_regex, views_str_regex, age_str_regex)
    msg = 'http://vimeo.com/29996808'
    check_re(regex, module_urltitle.handle_url(botmock, None, "#channel", msg, msg)[1])


@my_vcr.use_cassette
def test_liveleak(botmock):
    regex = 'Title: (.*?) by (.*?) \[%s views - Jul-23-2013 - tags\: sword, cut, hand, watermelon, fail\]' % (views_str_regex)
    msg = 'http://www.liveleak.com/view?i=f8e_1374614129'
    check_re(regex, module_urltitle.handle_url(botmock, None, "#channel", msg, msg)[1])


@my_vcr.use_cassette
def test_ebay(botmock):
    msg = 'https://ebay.com/itm/390629338875'
    regex = 'Title: .*? \[\d+\.\de \(postage \d+\.\de\) - over \d+ available - ships from .*?\]'
    check_re(regex, module_urltitle.handle_url(botmock, None, "#channel", msg, msg)[1])


@my_vcr.use_cassette
def test_ebay_cgi(botmock):
    msg = 'http://cgi.ebay.co.uk/ws/eBayISAPI.dll?ViewItem&item=121136837564'
    regex = 'Title: .*? \[\d+\.\de - over \d+ available - ships from .*?\]'
    check_re(regex, module_urltitle.handle_url(botmock, None, "#channel", msg, msg)[1])


@my_vcr.use_cassette
def test_dx(botmock):
    regex = 'Title: Wireless Bluetooth Audio Music Receiver Adapter - Black \[\d+\.\d+e - \[\** *\] - \d+ reviews\]'
    msg = 'http://dx.com/p/wireless-bluetooth-audio-music-receiver-adapter-black-151659'
    check_re(regex, module_urltitle.handle_url(botmock, None, "#channel", msg, msg)[1])


@my_vcr.use_cassette
def test_alko(botmock):
    regex = 'Title: Sandels A tölkki \[\d\.\d\de, \d\.\d\dl, \d\.\d\%\, \d\.\d\de/l, \d\.\d\de/annos, oluet]'
    msg = 'http://www.alko.fi/tuotteet/798684/'
    check_re(regex, module_urltitle.handle_url(botmock, None, "#channel", msg, msg)[1])


@my_vcr.use_cassette
def test_google_play_music(botmock):
    msg = 'https://play.google.com/music/m/Tkyqfh5koeirtbi76b2tsee6e2y'
    responses = [('#channel', 'Title: Villiviini - Ultra Bra'), None]
    ok_(module_urltitle.handle_url(botmock, None, "#channel", msg, msg) in responses)


@my_vcr.use_cassette
def test_steamstore(botmock):
    msg = 'http://store.steampowered.com/app/440/'
    title = 'Title: Team Fortress 2 | Free to play'
    eq_(title, module_urltitle.handle_url(botmock, None, "#channel", msg, msg)[1])


@my_vcr.use_cassette
def test_meta_fragment(botmock):
    msg = 'https://www.redbullsoundselect.com/events'
    title = 'Title: Events | Red Bull Sound Select'
    eq_(title, module_urltitle.handle_url(botmock, None, "#channel", msg, msg)[1])


# Only a couple of tests and 1.5s sleep because rate is limited to
# 1 request/sec/ip; if an API breaks, it often breaks completely.

@my_vcr.use_cassette
def test_discogs_release(botmock):
    title = "Rick Astley - Never Gonna Give You Up - (1987) - PB 41447"
    msg = "http://www.discogs.com/release/249504"
    eq_(("#channel", "Title: %s" % title), module_urltitle.handle_url(botmock, None, "#channel", msg, msg))
    sleep(3)


@my_vcr.use_cassette
def test_discogs_user(botmock):
    regex = ".+Rating avg: \d\.\d\d \(total \d+\)"
    msg = "http://www.discogs.com/user/rodneyfool"
    check_re(regex, module_urltitle.handle_url(botmock, None, "#channel", msg, msg)[1])


@my_vcr.use_cassette
def test_gfycat_reddit_title(botmock):
    regex = "Title: California Sunset \(/r/NatureGifs\) 1280x720@29fps \d+ views"
    msg = "http://www.gfycat.com/ZanyFragrantHoneyeater"
    check_re(regex, module_urltitle.handle_url(botmock, None, "#channel", msg, msg)[1])


@my_vcr.use_cassette
def test_gfycat_own_title(botmock):
    regex = "Title: Star Trail's in the Desert 632x480@30fps \d+ views"
    msg = "https://www.gfycat.com/EcstaticWelllitHarpseal"
    check_re(regex, module_urltitle.handle_url(botmock, None, "#channel", msg, msg)[1])


# @my_vcr.use_cassette
# def test_gfycat_direct_url(botmock):
#     regex = "Title: \(/r/NatureGifs\) 270x480@30fps \d+ views"
#     msg = "https://zippy.gfycat.com/QualifiedSpanishAmericankestrel.webm"
