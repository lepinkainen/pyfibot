# -*- coding: utf-8 -*-
import bot_mock
from pyfibot.modules import module_openweather
from utils import check_re


bot = bot_mock.BotMock()


def test_weather():
    regex = u'(Lappeenranta, (Finland|FI): Temperature: -?\d+.\d\xb0C, feels like: -?\d+.\d\xb0C, wind: \d+.\d m/s, humidity: \d+%, pressure: \d+ hPa, cloudiness: \d+%)|(Error: API error.)'
    check_re(regex, module_openweather.command_weather(bot, None, "#channel", 'lappeenranta')[1])


def test_forecast():
    regex = u'(Lappeenranta, (Finland|FI): tomorrow: -?\d+.\d - -?\d+.\d \xb0C \(.*?\), in 2 days: -?\d+.\d - -?\d+.\d \xb0C \(.*?\), in 3 days: -?\d+.\d - -?\d+.\d \xb0C \(.*?\))|(Error: API error.)'
    check_re(regex, module_openweather.command_forecast(bot, None, "#channel", 'lappeenranta')[1])
