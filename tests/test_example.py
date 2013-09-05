from nose.tools import eq_

import bot_mock


def test_example():
    assert True


def test_botmock():
    bot = bot_mock.BotMock()
    eq_(('#channel', 'Foo'), bot.say("#channel", "Foo"))


def test_module_bmi():
    from pyfibot.modules import module_bmi
    bot = bot_mock.BotMock()
    eq_(('#channel', 'your bmi is 27.76 which is overweight (from 25 to 30)'), module_bmi.command_bmi(bot, None, "#channel", "175/85"))

