# -*- coding: utf-8 -*-
from pyfibot.util.pyfiurl import grab

needScheme = True


def testLeadingSpaces():
    """Leading spaces before URL"""
    assert ["http://tomtom.foobar.org/"] == grab(
        "     http://tomtom.foobar.org/", needScheme
    )
    assert ["http://www.foobi.org/saatoimia"] == grab(
        "  http://www.foobi.org/saatoimia", needScheme
    )


def testTrailingSpaces():
    """Trailing spaces after URL"""
    assert ["http://tomtom.foobar.org/"] == grab(
        "http://tomtom.foobar.org/     ", needScheme
    )
    assert ["http://www.foobi.org/saatoimia"] == grab(
        "http://www.foobi.org/saatoimia    ", needScheme
    )


def testLongURL():
    """A long URL-like string"""
    assert [] == grab(
        "www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www",
        needScheme,
    )


def testQuestionMarkURI():
    """An URI with a question mark"""
    assert ["http://www.bdog.fi/cgi-bin/netstore/tuotehaku.pl?tuoteryhma=16"] == grab(
        "http://www.bdog.fi/cgi-bin/netstore/tuotehaku.pl?tuoteryhma=16", needScheme
    )


def testLeadingText():
    """Leading text"""
    assert ["http://www.technikfoo.de/mai"] == grab(
        "here it is: http://www.technikfoo.de/mai", needScheme
    )


def testLeadingAndTrailingText():
    """Leading and trailing text"""
    assert ["http://123.123.123.123"] == grab(
        "fooasdf asdf a http://123.123.123.123 asdfasdf", needScheme
    )


def testIP():
    """http URI with an ip number"""
    assert ["http://234.234.234.234"] == grab("http://234.234.234.234", needScheme)


def testFoobarIP():
    """ip number-like text"""
    assert [] == grab(
        "http://11123.123.123.123/eisaa http://123.123.123.12345/eisaa", needScheme
    )


def test2URIs():
    """2 URIs on same text"""
    assert ["http://foobar.fi/1234{}[]{}", "http://127.0.0.1/"] == grab(
        "http://foobar.fi/1234{}[]{} sadfljs dlfkjsd lf;asdf http://127.0.0.1/",
        needScheme,
    )


def testIPv6():
    """IPv6 URL with scheme"""
    assert ["http://[2001:a68:104:1337:250:daff:fe72:871c]/toimia"] == grab(
        "foo http://[2001:a68:104:1337:250:daff:fe72:871c]/toimia", needScheme
    )


def testIPv6noscheme():
    """IPv6 URL without a scheme"""
    if needScheme:
        return
    assert ["[2001:a68:104:1337:250:daff:fe72:871c]/toimia"] == grab(
        "foo [2001:a68:104:1337:250:daff:fe72:871c]/toimia", needScheme
    )


def testNoScheme():
    """URI without a scheme"""
    if needScheme:
        return
    assert ["123.123.123.123"] == grab("123.123.123.123", needScheme)


def testRedirect():
    """Redirect URL"""
    assert [
        "http://rediretinmyurl.com/http://dest.url.org/1/2/3/4?434",
        "http://secondurl.com",
        "ftp://1.2.3.4/adsfasdf",
    ] == grab(
        "http://rediretinmyurl.com/http://dest.url.org/1/2/3/4?434 http://secondurl.com ftp://1.2.3.4/adsfasdf",
        needScheme,
    )


def testAnchor():
    """Link with an anchor tag"""
    assert ["http://foo.com/page.html#anchor"] == grab(
        "http://foo.com/page.html#anchor", needScheme
    )


def testScandinavian():
    """Test åäö"""
    assert [
        "http://www.hs.fi/kotimaa/artikkeli/Äidin+avovaimosta+lapsen+toinen+huoltaja+KKOn+päätöksellä/1135253379084"
    ] == grab(
        "http://www.hs.fi/kotimaa/artikkeli/Äidin+avovaimosta+lapsen+toinen+huoltaja+KKOn+päätöksellä/1135253379084",
        needScheme,
    )


def testBlocks():
    """Test blocks"""
    assert [
        "http://link1.com",
        "http://link2.com",
        "http://link3.com",
        "http://link4.com",
        "http://link5.com",
    ] == grab(
        "(http://link1.com) <http://link2.com> \"http://link3.com\" 'http://link4.com' [http://link5.com]",
        needScheme,
    )
