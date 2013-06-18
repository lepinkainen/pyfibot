from nose.tools import eq_
import bot_mock
from pyfibot.modules import module_urltitle


bot = bot_mock.BotMock()


def test_imdb_ignore():
    msg = "http://www.imdb.com/title/tt1772341/"
    module_urltitle.init(bot)
    eq_(None, module_urltitle.handle_url(bot, None, "#channel", msg, msg))


def test_spotify_ignore():
    msg = "http://open.spotify.com/artist/4tuiQRw9bC9HZhSFJEJ9Mz"
    module_urltitle.init(bot)
    eq_(None, module_urltitle.handle_url(bot, None, "#channel", msg, msg))


def test_manual_ignore():
    msg = "- foofoo http://www.youtube.com/"
    module_urltitle.init(bot)
    eq_(None, module_urltitle.handle_url(bot, None, "#channel", msg, msg))


def disabledtest_youtube_general():
    msg = "http://www.youtube.com/watch?v=S92fTz_-kQE"
    module_urltitle.init(bot)
    eq_("#channel|your bmi is 27.76 which is overweight (from 25 to 30)", module_urltitle.handle_url(bot, None, "#channel", msg, msg))

