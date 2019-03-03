# -*- coding: utf-8 -*-
from nose.tools import eq_
import bot_mock
from pyfibot.modules import module_wolfram_alpha
from utils import check_re
import pytest
from vcr import VCR

my_vcr = VCR(
    path_transformer=VCR.ensure_suffix(".yaml"),
    cassette_library_dir="tests/cassettes/",
    record_mode=pytest.config.getoption("--vcrmode"),
)


@pytest.fixture
def botmock():
    config = {
        "module_wolfram_alpha": {"appid": "3EYA3R-WVR6GJQWLH"}
    }  # unit-test only APPID, do not abuse kthxbai
    bot = bot_mock.BotMock(config=config)
    return bot


@my_vcr.use_cassette
def test_simple(botmock):
    module_wolfram_alpha.init(botmock)
    query = "42"
    # Wolfram Alpha seems to randomly return also Roman numerals
    regex = u"(42 = forty-two|forty-two = XLII)"
    result = module_wolfram_alpha.command_wa(botmock, None, "#channel", query)[1]
    check_re(regex, result)


@my_vcr.use_cassette
def test_complex(botmock):
    query = "answer to the life universe and everything"
    target = (
        "#channel",
        u"Answer to the Ultimate Question of Life, the Universe, and Everything = 42 | (according to the book The Hitchhiker's Guide to the Galaxy, by Douglas Adams)",
    )
    result = module_wolfram_alpha.command_wa(botmock, None, "#channel", query)
    eq_(target, result)
