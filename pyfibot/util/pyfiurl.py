#!/usr/bin/python
# -*- coding: utf-8 -*-
## (c)2004 Timo Reunanen <parker _et_ wolfenstein _dit_ org>

## Thanks to Shrike for helping this :)

## Made by #python.fi ppl for python ppl

"""Find absolute URLs from strings"""

__version__ = "3.0.3"

import re
from UserString import UserString
import string
import sys

_countrycodes=['ac', 'ad', 'ae', 'af', 'ag', 'ai', 'al', 'am', 'an', 'ao',
               'aq', 'ar', 'as', 'at', 'au', 'aw', 'ax', 'az', 'ba', 'bb',
               'bd', 'be', 'bf', 'bg', 'bh', 'bi', 'bj', 'bm', 'bn', 'bo',
               'br', 'bs', 'bt', 'bv', 'bw', 'by', 'bz', 'ca', 'cc', 'cd',
               'cf', 'cg', 'ch', 'ci', 'ck', 'cl', 'cm', 'cn', 'co', 'cr',
               'cs', 'cu', 'cv', 'cx', 'cy', 'cz', 'de', 'dj', 'dk', 'dm',
               'do', 'dz', 'ec', 'ee', 'eg', 'eh', 'er', 'es', 'et', 'fi',
               'fj', 'fk', 'fm', 'fo', 'fr', 'ga', 'gb', 'gd', 'ge', 'gf',
               'gg', 'gh', 'gi', 'gl', 'gm', 'gn', 'gp', 'gq', 'gr', 'gs',
               'gt', 'gu', 'gw', 'gy', 'hk', 'hm', 'hn', 'hr', 'ht', 'hu',
               'id', 'ie', 'il', 'im', 'in', 'io', 'iq', 'ir', 'is', 'it',
               'je', 'jm', 'jo', 'jp', 'ke', 'kg', 'kh', 'ki', 'km', 'kn',
               'kp', 'kr', 'kw', 'ky', 'kz', 'la', 'lb', 'lc', 'li', 'lk',
               'lr', 'ls', 'lt', 'lu', 'lv', 'ly', 'ma', 'mc', 'md', 'mg',
               'mh', 'mk', 'ml', 'mm', 'mn', 'mo', 'mp', 'mq', 'mr', 'ms',
               'mt', 'mu', 'mv', 'mw', 'mx', 'my', 'mz', 'na', 'nc', 'ne',
               'nf', 'ng', 'ni', 'nl', 'no', 'np', 'nr', 'nu', 'nz', 'om',
               'pa', 'pe', 'pf', 'pg', 'ph', 'pk', 'pl', 'pm', 'pn', 'pr',
               'ps', 'pt', 'pw', 'py', 'qa', 're', 'ro', 'ru', 'rw', 'sa',
               'sb', 'sc', 'sd', 'se', 'sg', 'sh', 'si', 'sj', 'sk', 'sl',
               'sm', 'sn', 'so', 'sr', 'st', 'sv', 'sy', 'sz', 'tc', 'td',
               'tf', 'tg', 'th', 'tj', 'tk', 'tl', 'tm', 'tn', 'to', 'tp',
               'tr', 'tt', 'tv', 'tw', 'tz', 'ua', 'ug', 'uk', 'um', 'us',
               'uy', 'uz', 'va', 'vc', 've', 'vg', 'vi', 'vn', 'vu', 'wf',
               'ws', 'ye', 'yt', 'yu', 'za', 'zm', 'zw', 'aero', 'biz', 'com',
               'coop', 'edu', 'gov', 'info', 'int', 'mil', 'museum', 'name',
               'net', 'org', 'pro', 'me', 'mobi', 'xxx']

_schemes = ['http://', 'https://', 'ftp://', 'svn://']

## domainlabel   = alphanum | alphanum *( alphanum | "-" ) alphanum
_domainlabel=r'''
(?:
  [a-z0-9]
  |
  (?:
    [a-z0-9]
    [a-z0-9-]*?
    [a-z0-9]
  )
)
'''

## toplabel      = alpha | alpha *( alphanum | "-" ) alphanum
_toplabel=r'''
(?P<toplabel>
  (?:
    [a-z]
    [a-z0-9-]*
    [a-z0-9]
  )
  |
  (?: [a-z] )
)
'''


## hostname      = *( domainlabel "." ) toplabel [ "." ]
_hostname=r'''
(?P<hostname>
  (?: %(_domainlabel)s [.])+
  %(_toplabel)s
)
''' % globals()

_ipv4=r"""
(?P<ipv4>
  (?:(?<=[^0-9]) | \A)                  ## Doesn't start with number
  (?:[0-9]{1,3}\.){3}[0-9]{1,3}         ## '123.123.123.123'
  (?![0-9])                             ## And doesn't end with number
)
"""

_singleNum=r"""[0-9a-f]{0,4}"""
_ipv6=r"""
(?:
  [[]                                    ## Start [
  (?P<ipv6>
    (?: %(_singleNum)s[:] ){2,7}         ## xxxx:xxxx:[xxxx:[xxxx:[xxxx:[xxxx:[xxxx:]]]]]
    %(_singleNum)s                       ## xxxx
  )
  []]                                    ## End ]
)
""" % globals()

## host          = hostname | IPv4address | IPv6address [ ":" port ]
_host=r'''
(?P<host>
  (?:                                   ## Must be one of these
    %(_hostname)s |                     
    %(_ipv4)s |
    %(_ipv6)s
  )
  (?:                                   ## Check if port is defined
    :
     (?P<port>
      [0-9]+
    )
  )?
)
''' % globals()

## def emacsHack():
##   pass
## "

validPathChars=[string.ascii_letters,
                string.digits,
                '/;?:@&=+$,%#'
                '-_.!~*()',
                'åäö[]<>{}^\|\'`–', ## not so valid but used
                ]

validUserinfoChars=[string.ascii_letters,
                    string.digits,
                    ';:&=+$,',
                    '-_.!~*()',
                    '%@'
                    ]

validPathChars=''.join(validPathChars)
validUserinfoChars=''.join(validUserinfoChars)

hostRe=re.compile(_host, re.VERBOSE | re.MULTILINE | re.I)

def grab(txt, needScheme=True):
    seekpos=0

    possibleUrls=[]

    ## Try to find all possible URI's 
    while 1:
        srch=hostRe.search(txt, seekpos)
        if not srch: break

        valid=False

        ## Find possible URI with valid hostname, ipv4 or ipv6
        if srch.group('host'):
            if srch.group('ipv4'):
                ## Check if it is valid ipv4
                ip=[x for x in srch.group('ipv4').split('.') if int(x) > 255]
                if ip == []:
                    valid=True
                    
            elif srch.group('hostname'):
                ## Check if valid country code
                if srch.group('toplabel') in _countrycodes:
                    valid=True

            elif srch.group('ipv6'):
                ## ipv6 is always valid :P (yeah right...) 
                valid=True

        if not valid:
            seekpos=srch.end('host')
            continue
        
        s=srch.start('host')
        e=srch.end('host')

        ## Check if there is userinfo in URI
        if s > 1 and txt[s-1]=='@':
            s-=1

            while s >= 0 and txt[s] in validUserinfoChars: s-=1

            s+=1

        ## Check if there is scheme
        schemeFound=False
        for scheme in _schemes:
            if txt[s-len(scheme):s] == scheme:
                s-=len(scheme)
                schemeFound=True
                break

        ## If scheme neede and no scheme found, skip it
        if needScheme and not schemeFound:
            seekpos=srch.end('host')
            continue

        ## Try to figure out rest of URI
        while e < len(txt) and txt[e] in validPathChars: e+=1


        ## Some silly hack
        ns=s

        for v in [('<', '>'),('(', ')'), ('{', '}'), ('[', ']'), '"', "'"]:
            if type(v)==tuple:
                sc,ec=v
            else:
                sc=ec=v

            if txt[ns-len(sc):].startswith(sc):
                if txt[e-len(ec):].startswith(ec):
                    e-=len(ec)

        possibleUrls.append(txt[s:e])

        seekpos=e

    return possibleUrls

def unitTest():
    import unittest
    class TestPRUL(unittest.TestCase):
        def setUp(self):
            self.needScheme = True

        def testLeadingSpaces(self):
            """Leading spaces before URL"""
            self.assertEqual(["http://tomtom.foobar.org/"], grab('     http://tomtom.foobar.org/', self.needScheme))
            self.assertEqual(["http://www.foobi.org/saatoimia"], grab('  http://www.foobi.org/saatoimia', self.needScheme))

        def testTrailingSpaces(self):
            """Trailing spaces after URL"""
            self.assertEqual(["http://tomtom.foobar.org/"], grab('http://tomtom.foobar.org/     ', self.needScheme))
            self.assertEqual(["http://www.foobi.org/saatoimia"], grab('http://www.foobi.org/saatoimia    ', self.needScheme))

        def testLongURL(self):
            """A long URL-like string"""
            self.assertEqual([], grab('www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www.www', self.needScheme))

        def testQuestionMarkURI(self):
            """An URI with a question mark"""
            self.assertEqual(["http://www.bdog.fi/cgi-bin/netstore/tuotehaku.pl?tuoteryhma=16"],  grab('http://www.bdog.fi/cgi-bin/netstore/tuotehaku.pl?tuoteryhma=16', self.needScheme))

        def testLeadingText(self):
            """Leading text"""
            self.assertEqual(["http://www.technikfoo.de/mai"], grab('here it is: http://www.technikfoo.de/mai', self.needScheme))

        def testLeadingAndTrailingText(self):
            """Leading and trailing text"""
            self.assertEqual(["http://123.123.123.123"], grab('fooasdf asdf a http://123.123.123.123 asdfasdf', self.needScheme))

        def testIP(self):
            """http URI with an ip number"""
            self.assertEqual(["http://234.234.234.234"], grab('http://234.234.234.234', self.needScheme))

        def testFoobarIP(self):
            """ip number-like text"""
            self.assertEqual([], grab('http://11123.123.123.123/eisaa http://123.123.123.12345/eisaa', self.needScheme))

        def test2URIs(self):
            """2 URIs on same text"""
            self.assertEqual(["http://foobar.fi/1234{}[]{}", "http://127.0.0.1/"], grab('http://foobar.fi/1234{}[]{} sadfljs dlfkjsd lf;asdf http://127.0.0.1/', self.needScheme))
            
        def testIPv6(self):
            """IPv6 URL with scheme"""
            self.assertEqual(["http://[2001:a68:104:1337:250:daff:fe72:871c]/toimia"], grab('foo http://[2001:a68:104:1337:250:daff:fe72:871c]/toimia', self.needScheme))

        def testIPv6noscheme(self):
            """IPv6 URL without a scheme"""
            if self.needScheme: return
            
            self.assertEqual(["[2001:a68:104:1337:250:daff:fe72:871c]/toimia"], grab('foo [2001:a68:104:1337:250:daff:fe72:871c]/toimia', self.needScheme))

        def testNoScheme(self):
            """URI without a scheme"""
            if self.needScheme: return
            
            self.assertEqual(["123.123.123.123"], grab('123.123.123.123', self.needScheme))

        def testRedirect(self):
            """Redirect URL"""
            self.assertEqual(['http://rediretinmyurl.com/http://dest.url.org/1/2/3/4?434', 'http://secondurl.com', 'ftp://1.2.3.4/adsfasdf'], grab('http://rediretinmyurl.com/http://dest.url.org/1/2/3/4?434 http://secondurl.com ftp://1.2.3.4/adsfasdf', self.needScheme))

        def testAnchor(self):
            """Link with an anchor tag"""
            self.assertEqual(['http://foo.com/page.html#anchor'], grab('http://foo.com/page.html#anchor', self.needScheme))

        def testScandinavian(self):
            """Test åäö"""
            self.assertEqual(['http://www.hs.fi/kotimaa/artikkeli/Äidin+avovaimosta+lapsen+toinen+huoltaja+KKOn+päätöksellä/1135253379084'], grab('http://www.hs.fi/kotimaa/artikkeli/Äidin+avovaimosta+lapsen+toinen+huoltaja+KKOn+päätöksellä/1135253379084', self.needScheme))

        def testBlocks(self):
            """Test blocks"""
            self.assertEqual(['http://link1.com',
                              'http://link2.com',
                              'http://link3.com',
                              'http://link4.com',
                              'http://link5.com',
                              ], grab('(http://link1.com) <http://link2.com> "http://link3.com" \'http://link4.com\' [http://link5.com]', self.needScheme))

    # run unittest
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestPRUL))
    unittest.TextTestRunner(verbosity=2).run(suite)

def _main():
    if '--test' in sys.argv:
        unitTest()
        return

    needScheme='--noscheme' not in sys.argv
    
    for line in sys.stdin:
        for url in grab(line, needScheme):
            print url

if __name__ == '__main__':
    _main()
