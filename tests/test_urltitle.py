# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
from nose.tools import eq_
import bot_mock
from pyfibot.modules import module_urltitle
from utils import check_re

import pytest
from vcr import VCR

my_vcr = VCR(
    path_transformer=VCR.ensure_suffix(".yaml"),
    cassette_library_dir="tests/cassettes/",
    record_mode=pytest.config.getoption("--vcrmode"),
)

logging.basicConfig()  # you need to initialize logging, otherwise you will not see anything from vcrpy
vcr_log = logging.getLogger("vcr")
vcr_log.setLevel(logging.DEBUG)


@pytest.fixture
def botmock():
    bot = bot_mock.BotMock()
    module_urltitle.init(bot)
    return bot


lengh_str_regex = "\d+(h|m|s)(\d+(m))?(\d+s)?"
views_str_regex = "\d+(\.\d+)?(k|M|Billion|Trillion)?"
age_str_regex = "(FRESH|(\d+(\.\d+)?(y|d) ago))"


def __handle_url(botmock, msg):
    res = module_urltitle.handle_url(botmock, None, "#channel", msg, msg)
    if type(res) == tuple:
        return res[1]
    else:
        return res


@my_vcr.use_cassette
def test_spotify_ignore(botmock):
    msg = "http://open.spotify.com/artist/4tuiQRw9bC9HZhSFJEJ9Mz"
    assert __handle_url(botmock, msg) is None


@my_vcr.use_cassette
def test_manual_ignore(botmock):
    msg = "- foofoo http://www.youtube.com/"
    assert __handle_url(botmock, msg) is None


@my_vcr.use_cassette
def test_iltalehti(botmock):
    msg = "http://www.iltalehti.fi/ulkomaat/2013072917307393_ul.shtml"
    assert "Title: Saksassa syntyi jättivauva - yli kuusi kiloa!" == __handle_url(
        botmock, msg
    )


@my_vcr.use_cassette
def test_iltasanomat(botmock):
    msg = "http://www.iltasanomat.fi/viihde/art-1288596309269.html"
    assert (
        "Title: Muistatko Mari Sainion juontaman sarjan, josta sai palkinnoksi isdn-liittymän?"
        == __handle_url(botmock, msg)
    )


@my_vcr.use_cassette
def test_verkkokauppacom(botmock):
    msg = "http://www.verkkokauppa.com/fi/product/55124/dfbfn/Coca-Cola-Vanilla-USA-virvoitusjuoma-355-ml"
    regex = "Title: Coca-Cola Vanilla USA virvoitusjuoma 355 ml \| \d+,\d+ € \(.*?\)"
    check_re(regex, __handle_url(botmock, msg))


@my_vcr.use_cassette
def test_stackoverflow(botmock):
    msg = "http://stackoverflow.com/questions/6905508/python-search-html-document-for-capital-letters"
    assert (
        "Title: Python search HTML document for capital letters - 0pts - python/regex/coda/letters/capitalize"
        == __handle_url(botmock, msg)
    )


@my_vcr.use_cassette
def test_wiki_fi(botmock):
    msg = "http://fi.wikipedia.org/wiki/Kimi_Räikkönen"
    assert (
        "Title: Kimi-Matias Räikkönen on suomalainen autourheilija ja Formula 1 -sarjan maailmanmestari."
        == __handle_url(botmock, msg)
    )


@my_vcr.use_cassette
def test_wiki_en(botmock):
    msg = "http://en.wikipedia.org/wiki/IPhone"
    assert (
        "Title: iPhone is a line of smartphones designed and marketed by Apple Inc."
        == __handle_url(botmock, msg)
    )


@my_vcr.use_cassette
def test_imdb(botmock):
    regex = (
        "Title: Wreck-It Ralph \(2012\) - [\d.]{1,}/10 \(%s votes\) - .*"
        % views_str_regex
    )
    msg = "http://www.imdb.com/title/tt1772341/"
    check_re(regex, __handle_url(botmock, msg))


@my_vcr.use_cassette
def test_youtube(botmock):
    regex = "Title: (.*?) by (.*?) \[%s - %s views - %s( - age restricted)?\]" % (
        lengh_str_regex,
        views_str_regex,
        age_str_regex,
    )
    msg = "http://www.youtube.com/watch?v=awsolTK175c"
    module_urltitle.init(botmock)
    check_re(regex, __handle_url(botmock, msg))


@my_vcr.use_cassette
def test_vimeo(botmock):
    regex = "Title: (.*?) by (.*?) \[%s - %s likes - %s views - %s]" % (
        lengh_str_regex,
        views_str_regex,
        views_str_regex,
        age_str_regex,
    )
    msg = "http://vimeo.com/29996808"
    check_re(regex, __handle_url(botmock, msg))


@my_vcr.use_cassette
def test_liveleak(botmock):
    regex = (
        "Title: (.*?) by (.*?) \[%s views - Jul-23-2013 - tags\: sword, cut, hand, watermelon, fail\]"
        % (views_str_regex)
    )
    msg = "http://www.liveleak.com/view?i=f8e_1374614129"
    check_re(regex, __handle_url(botmock, msg))


@my_vcr.use_cassette
def test_ebay(botmock):
    msg = "https://ebay.com/itm/390629338875"
    regex = "Title: .*? \[\d+\.\de \(postage \d+\.\de\) - over \d+ available - ships from .*?\]"
    check_re(regex, __handle_url(botmock, msg))


@my_vcr.use_cassette
def test_ebay_cgi(botmock):
    msg = "http://cgi.ebay.co.uk/ws/eBayISAPI.dll?ViewItem&item=121136837564"
    regex = "Title: .*? \[\d+\.\de - over \d+ available - ships from .*?\]"
    check_re(regex, __handle_url(botmock, msg))


@my_vcr.use_cassette
def test_dx(botmock):
    regex = "Title: Wireless Bluetooth Audio Music R... \[\d+\.\d+e - \[\** *\] - \d+ reviews\]"
    msg = "http://dx.com/p/wireless-bluetooth-audio-music-receiver-adapter-black-151659"
    check_re(regex, __handle_url(botmock, msg))


@my_vcr.use_cassette
def test_alko(botmock):
    regex = "Title: Sandels A tölkki \[\d\.\d\de, \d\.\d\dl, \d\.\d\%\, \d\.\d\de/l, \d\.\d\de/annos, oluet]"
    msg = "http://www.alko.fi/tuotteet/798684/"
    check_re(regex, __handle_url(botmock, msg))


@my_vcr.use_cassette
def test_google_play_music(botmock):
    msg = "https://play.google.com/music/preview/Tkyqfh5koeirtbi76b2tsee6e2y"
    responses = ["Title: Villiviini - Ultra Bra", None]
    assert __handle_url(botmock, msg) in responses


@my_vcr.use_cassette
def test_steamstore(botmock):
    msg = "http://store.steampowered.com/app/440/"
    title = "Title: Team Fortress 2 | Free to play"
    eq_(title, __handle_url(botmock, msg))


@my_vcr.use_cassette
def test_meta_fragment(botmock):
    msg = "https://www.redbullsoundselect.com/events"
    title = "Title: Events | Red Bull Sound Select"
    eq_(title, __handle_url(botmock, msg))


# Only a couple of tests and 1.5s sleep because rate is limited to
# 1 request/sec/ip; if an API breaks, it often breaks completely.


@my_vcr.use_cassette
def test_discogs_release(botmock):
    title = "Rick Astley - Never Gonna Give You Up - (1987) - PB 41447"
    msg = "http://www.discogs.com/release/249504"
    assert "Title: %s" % title == __handle_url(botmock, msg)


@my_vcr.use_cassette
def test_discogs_user(botmock):
    regex = ".+Rating avg: \d\.\d\d \(total \d+\)"
    msg = "http://www.discogs.com/user/rodneyfool"
    check_re(regex, __handle_url(botmock, msg))


@my_vcr.use_cassette
def test_gfycat_reddit_title(botmock):
    regex = "Title: California Sunset \(/r/NatureGifs\) 1280x720@29fps \d+ views"
    msg = "http://www.gfycat.com/ZanyFragrantHoneyeater"
    check_re(regex, __handle_url(botmock, msg))


@my_vcr.use_cassette
def test_gfycat_own_title(botmock):
    regex = "Title: Star Trail's in the Desert 632x480@30fps \d+ views"
    msg = "https://www.gfycat.com/EcstaticWelllitHarpseal"
    check_re(regex, __handle_url(botmock, msg))


@my_vcr.use_cassette
def test_pythonorg(botmock):
    msg = "http://python.org"
    eq_("Title: Welcome to Python.org", __handle_url(botmock, msg))


@my_vcr.use_cassette
def test_github(botmock):
    msg = "https://github.com/lepinkainen/pyfibot"
    assert (
        "Title: GitHub - lepinkainen/pyfibot: Pyfibot the Python IRC bot"
        == __handle_url(botmock, msg)
    )


@my_vcr.use_cassette
def test_gfycat_direct_url(botmock):
    regex = "Title: \(/r/NatureGifs\) 270x480@30fps \d+ views"
    msg = "https://zippy.gfycat.com/QualifiedSpanishAmericankestrel.webm"
    check_re(regex, __handle_url(botmock, msg))


@my_vcr.use_cassette
def test_nettiauto(botmock):
    msg = "http://www.nettiauto.com/audi/s4/7695854"
    assert (
        "Title: Audi S4 [2004, 129 958 km, 4.2 l Bensiini, Manuaali, Neliveto]"
        == __handle_url(botmock, msg)
    )


# Test ignored titles
@my_vcr.use_cassette
def test_apina(botmock):
    msg = "http://apina.biz"
    assert __handle_url(botmock, msg) is None


@my_vcr.use_cassette
def test_salakuunneltua(botmock):
    msg = "http://salakuunneltua.fi"
    assert __handle_url(botmock, msg) is None


@my_vcr.use_cassette
def test_travis(botmock):
    msg = "http://travis-ci.org/"
    assert __handle_url(botmock, msg) is None


@my_vcr.use_cassette
def test_ubuntupaste(botmock):
    msg = "http://paste.ubuntu.com/"
    assert __handle_url(botmock, msg) is None


@my_vcr.use_cassette
def test_poliisifi(botmock):
    msg = "http://poliisi.fi/tietoa_poliisista/tiedotteet/1/1/merisotakoulun_upseerikokelas_menehtyi_ampuharjoituksessa_hangon_syndalenissa_42596"
    assert __handle_url(botmock, msg) is None
