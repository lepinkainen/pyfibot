from nose.tools import eq_

import bot_mock


def test_example():
    assert True


def test_botmock():
    bot = bot_mock.BotMock({})
    eq_(('#channel', 'Foo'), bot.say("#channel", "Foo"))


def test_factorymock():
    factory = bot_mock.FactoryMock({})
    bot = factory.find_bot_for_network('nerv')
    eq_('nerv', bot.factory.find_bot_for_network('nerv').network.alias)
    eq_('localhost', bot.factory.find_bot_for_network('localhost').network.alias)
    eq_(None, bot.factory.find_bot_for_network('not_found'))


def test_module_bmi():
    from pyfibot.modules import module_bmi
    bot = bot_mock.BotMock()
    eq_(('#channel', 'your bmi is 27.76 which is overweight (from 25 to 30)'), module_bmi.command_bmi(bot, None, "#channel", "175/85"))
