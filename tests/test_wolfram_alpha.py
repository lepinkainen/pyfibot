# -*- coding: utf-8 -*-
from nose.tools import eq_
import bot_mock
from pyfibot.modules import module_wolfram_alpha


config = {"module_wolfram_alpha":
          {"appid": "3EYA3R-WVR6GJQWLH"}}  # unit-test only APPID, do not abuse kthxbai

bot = bot_mock.BotMock(config)


def test_simple():
    module_wolfram_alpha.init(bot)
    query = "42"
    target = ("#channel", u"42 = forty-two")
    result = module_wolfram_alpha.command_wa(bot, None, "#channel", query)
    eq_(target, result)


def test_complex():
    query = "what is the airspeed of an unladen swallow?"
    target = ("#channel", u"estimated average cruising airspeed of an unladen European swallow = 11 m/s (meters per second) | (asked, but not answered, about a general swallow in the 1975 film Monty Python and the Holy Grail)")
    result = module_wolfram_alpha.command_wa(bot, None, "#channel", query)
    eq_(target, result)
