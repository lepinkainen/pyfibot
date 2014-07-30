# -*- coding: utf-8 -*-
from nose.tools import eq_
import bot_mock
from pyfibot.modules import module_urltitle


bot = bot_mock.BotMock()


def test_one():
    msg = "https://en.wikipedia.org/wiki/Hatfield–McCoy_feud"
    module_urltitle.init(bot)
    eq_(("#channel", u"Title: The Hatfield–McCoy feud involved two families of the West Virginia–Kentucky area along the Tug Fork of the Big Sandy River."), module_urltitle.handle_url(bot, None, "#channel", msg, msg))


def test_two():
    msg = "http://fi.wikipedia.org/wiki/DTMF"
    module_urltitle.init(bot)
    eq_(("#channel", u"Title: DTMF on puhelinlaitteissa käytetty numeroiden äänitaajuusvalintatapa."), module_urltitle.handle_url(bot, None, "#channel", msg, msg))


def test_three():
    msg = "http://en.wikipedia.org/wiki/Gender_performativity"
    module_urltitle.init(bot)
    eq_(("#channel", u"Title: Gender performativity is a term created by post-structuralist feminist philosopher Judith Butler in her 1990 book Gender Trouble, which has subsequently been used in a variety of academic fields."), module_urltitle.handle_url(bot, None, "#channel", msg, msg))


def test_four():
    msg = "http://en.wikipedia.org/wiki/Dynamo_(magician)"
    module_urltitle.init(bot)
    eq_(("#channel", u"Title: Steven Frayne, commonly known by his stage name \"Dynamo\", is an English magician, best known for his show Dynamo: Magician Impossible."), module_urltitle.handle_url(bot, None, "#channel", msg, msg))


def test_five():
    msg = "http://fi.wikipedia.org/wiki/David_Eddings"
    module_urltitle.init(bot)
    eq_(("#channel", u"Title: David Carroll Eddings oli yhdysvaltalainen kirjailija, joka kirjoitti useita suosittuja fantasiakirjoja."), module_urltitle.handle_url(bot, None, "#channel", msg, msg))


def test_six():
    msg = "http://fi.wikipedia.org/wiki/Birger_Ek"
    module_urltitle.init(bot)
    eq_(("#channel", u"Title: Rolf Birger Ek oli suomalainen lentäjä ja Mannerheim-ristin ritari."), module_urltitle.handle_url(bot, None, "#channel", msg, msg))


def test_seven():
    msg = "http://en.wikipedia.org/wiki/Ramon_Llull"
    module_urltitle.init(bot)
    eq_(("#channel", u"Title: Ramon Llull, T.O.S.F. was a Majorcan writer and philosopher, logician and a Franciscan tertiary."), module_urltitle.handle_url(bot, None, "#channel", msg, msg))


def test_eight():
    msg = "http://en.wikipedia.org/wiki/Lazarus_of_Bethany#In_culture"
    module_urltitle.init(bot)
    eq_(("#channel", u"Title: Lazarus of Bethany, also known as Saint Lazarus or Lazarus of the Four Days, is the subject of a prominent miracle attributed to Jesus in the Gospel of John, in which Jesus restores him to life four d..."), module_urltitle.handle_url(bot, None, "#channel", msg, msg))


def test_nine():
    msg = "http://fi.wikipedia.org/wiki/Kimi_Räikkönen"
    module_urltitle.init(bot)
    eq_(("#channel", u"Title: Kimi-Matias Räikkönen on suomalainen autourheilija ja Formula 1:n maailmanmestari."), module_urltitle.handle_url(bot, None, "#channel", msg, msg))


def test_ten():
    msg = 'http://en.wikipedia.org/wiki/802.11ac'
    module_urltitle.init(bot)
    eq_(("#channel", u"Title: IEEE 802.11ac is a wireless networking standard in the 802.11 family, developed in the IEEE Standards Association process, providing high-throughput wireless local area networks on the 5\xa0GHz band."), module_urltitle.handle_url(bot, None, "#channel", msg, msg))


def test_eleven():
    msg = 'http://en.wikipedia.org/wiki/Edison_Arantes_do_Nascimento'
    module_urltitle.init(bot)
    eq_(("#channel", u"Title: Edson Arantes do Nascimento, who is better known as Pelé, is a retired Brazilian footballer who is widely regarded to be the best football player of all time."), module_urltitle.handle_url(bot, None, "#channel", msg, msg))
