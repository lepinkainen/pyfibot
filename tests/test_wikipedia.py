# -*- coding: utf-8 -*-
from nose.tools import eq_
import bot_mock
from pyfibot.modules import module_urltitle

import pytest
from vcr import VCR

my_vcr = VCR(
    path_transformer=VCR.ensure_suffix(".yaml"),
    cassette_library_dir="tests/cassettes/",
    record_mode=pytest.config.getoption("--vcrmode"),
)


@pytest.fixture
def botmock():
    bot = bot_mock.BotMock()
    module_urltitle.init(bot)
    return bot


@my_vcr.use_cassette()
def test_one(botmock):
    msg = "https://en.wikipedia.org/wiki/Hatfield–McCoy_feud"
    assert (
        "#channel",
        "Title: The Hatfield\u2013McCoy feud, also described by journalists as the Hatfield\u2013McCoy war, involved two rural American families of the West Virginia\u2013Kentucky area along the Tug Fork of the Big Sandy River in the years 1863\u20131891.",
    ) == module_urltitle.handle_url(botmock, None, "#channel", msg, msg)


@my_vcr.use_cassette()
def test_two(botmock):
    msg = "http://fi.wikipedia.org/wiki/DTMF"
    assert (
        "#channel",
        "Title: DTMF on puhelinlaitteissa k\xe4ytetty numeroiden \xe4\xe4nitaajuusvalinta.",
    ) == module_urltitle.handle_url(botmock, None, "#channel", msg, msg)


@my_vcr.use_cassette()
def test_three(botmock):
    msg = "http://en.wikipedia.org/wiki/Gender_performativity"
    assert (
        "#channel",
        "Title: The social construction of gender is a theory in feminism and sociology about the manifestation of cultural origins, mechanisms, and corollaries of gender perception and expression in the context of interpersonal and group social interaction.",
    ) == module_urltitle.handle_url(botmock, None, "#channel", msg, msg)


@my_vcr.use_cassette()
def test_four(botmock):
    msg = "http://en.wikipedia.org/wiki/Dynamo_(magician)"
    eq_(
        (
            "#channel",
            "Title: Steven Frayne, better known by his stage name Dynamo, is a British magician born in Bradford, West Yorkshire.",
        ),
        module_urltitle.handle_url(botmock, None, "#channel", msg, msg),
    )


@my_vcr.use_cassette()
def test_five(botmock):
    msg = "http://fi.wikipedia.org/wiki/David_Eddings"
    eq_(
        (
            "#channel",
            "Title: David Carroll Eddings oli yhdysvaltalainen kirjailija, joka kirjoitti useita suosittuja fantasiakirjoja.",
        ),
        module_urltitle.handle_url(botmock, None, "#channel", msg, msg),
    )


@my_vcr.use_cassette()
def test_six(botmock):
    msg = "http://fi.wikipedia.org/wiki/Birger_Ek"
    module_urltitle.init(botmock)
    eq_(
        (
            "#channel",
            "Title: Rolf Birger Ek oli suomalainen lentäjä ja Mannerheim-ristin ritari.",
        ),
        module_urltitle.handle_url(botmock, None, "#channel", msg, msg),
    )


@my_vcr.use_cassette()
def test_seven(botmock):
    msg = "http://en.wikipedia.org/wiki/Ramon_Llull"
    eq_(
        (
            "#channel",
            "Title: Ramon Llull was a mathematician, polymath, philosopher, logician, writer and mystic from the Kingdom of Majorca.",
        ),
        module_urltitle.handle_url(botmock, None, "#channel", msg, msg),
    )


@my_vcr.use_cassette()
def test_eight(botmock):
    msg = "https://en.wikipedia.org/wiki/Byzantine_art#Periods"
    eq_(
        (
            "#channel",
            "Title: Byzantine art comprises the body of Christian Greek artistic products of the Eastern Roman Empire, as well as the nations and states that inherited culturally from the empire.",
        ),
        module_urltitle.handle_url(botmock, None, "#channel", msg, msg),
    )


@my_vcr.use_cassette()
def test_nine(botmock):
    msg = "http://fi.wikipedia.org/wiki/Kimi_Räikkönen"
    eq_(
        (
            "#channel",
            "Title: Kimi-Matias Räikkönen on suomalainen autourheilija ja Formula 1 -sarjan maailmanmestari.",
        ),
        module_urltitle.handle_url(botmock, None, "#channel", msg, msg),
    )


@my_vcr.use_cassette()
def test_ten(botmock):
    msg = "http://en.wikipedia.org/wiki/802.11ac"
    eq_(
        (
            "#channel",
            "Title: IEEE 802.11ac-2013 or 802.11ac is a wireless networking standard in the 802.11 set of protocols, providing high-throughput wireless local area networks on the 5\xa0GHz band.",
        ),
        module_urltitle.handle_url(botmock, None, "#channel", msg, msg),
    )


@my_vcr.use_cassette()
def test_eleven(botmock):
    msg = "http://en.wikipedia.org/wiki/Edison_Arantes_do_Nascimento"
    eq_(
        (
            "#channel",
            "Title: Edson Arantes do Nascimento, known as Pel\xe9, is a Brazilian former professional footballer who played as a forward.",
        ),
        module_urltitle.handle_url(botmock, None, "#channel", msg, msg),
    )


@my_vcr.use_cassette()
def test_twelve(botmock):
    msg = "http://en.wikipedia.org/wiki/Mr._Bean"
    eq_(
        (
            "#channel",
            "Title: Mr. Bean is a British sitcom created by Rowan Atkinson and Richard Curtis, produced by Tiger Aspect and starring Atkinson as the title character.",
        ),
        module_urltitle.handle_url(botmock, None, "#channel", msg, msg),
    )
