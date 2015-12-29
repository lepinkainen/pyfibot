# .-*- encoding: utf-8 -*-
from __future__ import unicode_literals
import bot_mock
from pyfibot.modules.module_spotify import handle_privmsg

from utils import check_re
import pytest
from vcr import VCR
my_vcr = VCR(path_transformer=VCR.ensure_suffix('.yaml'),
             cassette_library_dir="tests/cassettes/",
             record_mode=pytest.config.getoption("--vcrmode"))

@pytest.fixture
def botmock():
    bot = bot_mock.BotMock()
    return bot


@my_vcr.use_cassette
def test_spotify_track(botmock):
    msg = 'spotify:track:46c5HqyYtOkpjdp193KCln'
    title = '[Spotify] Ultra Bra - Sinä päivänä kun synnyin - Heikko valo'
    assert ('#channel', title) == handle_privmsg(botmock, None, '#channel', msg)


@my_vcr.use_cassette
def test_http_artist(botmock):
    msg = 'http://open.spotify.com/artist/3MXhtYDNuzQQmLfOKFgPiI'
    regex = '\[Spotify\] Einojuhani Rautavaara( \(Genre: \S.+\))?'
    check_re(regex, handle_privmsg(botmock, None, '#channel', msg)[1])


@my_vcr.use_cassette
def test_http_album(botmock):
    msg = 'http://open.spotify.com/album/5O8MKoOZoTK1JfD1tAN2TA'
    title = '[Spotify] Organ - Nekrofiilis (2001)'
    assert ('#channel', title) == handle_privmsg(botmock, None, '#channel', msg)
