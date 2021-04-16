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


lengh_str_regex = r"\d+(h|m|s)(\d+(m))?(\d+s)?"
views_str_regex = r"\d+(\.\d+)?(k|M|Billion|Trillion)?"
age_str_regex = r"(FRESH|(\d+(\.\d+)?(y|d) ago))"


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
    msg = "https://www.iltalehti.fi/ulkomaat/a/2013072917307393"
    assert "Title: Saksassa syntyi jättivauva - yli kuusi kiloa!" == __handle_url(
        botmock, msg
    )


@my_vcr.use_cassette
def test_iltasanomat(botmock):
    msg = "https://www.is.fi/tv-ja-elokuvat/art-2000007925056.html"
    assert (
        "Title: The Voice of Finlandin finalistinelikko on selvill\xe4!"
        == __handle_url(botmock, msg)
    )


@my_vcr.use_cassette
def test_stackoverflow(botmock):
    msg = "http://stackoverflow.com/questions/6905508/python-search-html-document-for-capital-letters"
    assert (
        "Title: Python search HTML document for capital letters - 0pts - python/regex/coda/letters/capitalize"
        == __handle_url(botmock, msg)
    )


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
def test_ebay_cgi(botmock):
    msg = "http://cgi.ebay.co.uk/ws/eBayISAPI.dll?ViewItem&item=121136837564"
    regex = "Title: .*? \[\d+\.\de - over \d+ available - ships from .*?\ - ENDED]"
    check_re(regex, __handle_url(botmock, msg))


@my_vcr.use_cassette
def test_steamstore(botmock):
    msg = "http://store.steampowered.com/app/440/"
    title = "Title: Team Fortress 2 on Steam"
    eq_(title, __handle_url(botmock, msg))


@my_vcr.use_cassette
def test_pythonorg(botmock):
    msg = "http://python.org"
    eq_("Title: Welcome to Python.org", __handle_url(botmock, msg))


@my_vcr.use_cassette
def test_github(botmock):
    msg = "https://github.com/lepinkainen/pyfibot"
    assert (
        "Title: lepinkainen/pyfibot"
        == __handle_url(botmock, msg)
    )


# Test ignored titles
@my_vcr.use_cassette
def test_apina(botmock):
    msg = "http://apina.biz"
    assert __handle_url(botmock, msg) is None


@my_vcr.use_cassette
def test_poliisifi(botmock):
    msg = "http://poliisi.fi/tietoa_poliisista/tiedotteet/1/1/merisotakoulun_upseerikokelas_menehtyi_ampuharjoituksessa_hangon_syndalenissa_42596"
    assert __handle_url(botmock, msg) is None
