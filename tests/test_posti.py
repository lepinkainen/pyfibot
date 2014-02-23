# -*- coding: utf-8 -*-
# from nose.tools import eq_
import bot_mock
from pyfibot.modules.module_posti import command_posti
from utils import check_re


bot = bot_mock.BotMock()


def test_posti():
    '''11d 1h 45m ago - Item delivered to the recipient. - TAALINTEHDAS 25900'''
    regex = u'(\d+d\ )?(\d+h\ )?(\d+m )?ago - (.*?) - (.*? )?(\d+)'
    check_re(regex, command_posti(bot, 'example!example@example.com', '#example', 'JJFI')[1])
