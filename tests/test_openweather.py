# -*- coding: utf-8 -*-
# from tests import bot_mock
# from pyfibot.modules import module_openweather
# from utils import check_re
# import pytest
# from vcr import VCR
# my_vcr = VCR(path_transformer=VCR.ensure_suffix('.yaml'),
#              cassette_library_dir="tests/cassettes/",
#              filter_query_parameters=['appid'])  # censor appid from query


# @pytest.fixture
# def botmock():
#     bot = bot_mock.BotMock()
#     module_openweather.init(bot)
#     return bot


# @my_vcr.use_cassette
# def test_weather(botmock):
#     regex = u'(Lappeenranta, (Finland|FI): Temperature: -?\d+.\d\xb0C, feels like: -?\d+.\d\xb0C, wind: \d+.\d m/s, humidity: \d+%, pressure: \d+ hPa, cloudiness: \d+%)|(Error: API error.)'
#     check_re(regex, module_openweather.command_weather(botmock, None, "#channel", 'lappeenranta')[1])


# @my_vcr.use_cassette
# def test_forecast(botmock):
#     regex = u'(Lappeenranta, (Finland|FI): tomorrow: -?\d+.\d - -?\d+.\d \xb0C \(.*?\), in 2 days: -?\d+.\d - -?\d+.\d \xb0C \(.*?\), in 3 days: -?\d+.\d - -?\d+.\d \xb0C \(.*?\))|(Error: API error.)'
#     check_re(regex, module_openweather.command_forecast(botmock, None, "#channel", 'lappeenranta')[1])
