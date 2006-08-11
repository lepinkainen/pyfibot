#!/usr/bin/python
# -*- coding: iso8859-1 -*-
## (c)2004 Timo Reunanen <parker _et_ wolfenstein _dit_ org>

import time
import re

_exact=r'''
^
(?P<hour> \d{1,2})    ## hour
[:.]
(?P<min> \d{2})       ## minutes
(?:
  [:.]
  (?P<sec>\d{2} )     ## secods (optional)
)?
$
'''

_add=r'''
^
[+]
(?:                   ## hour
  (?P<hour> \d+)+h    ## syntax: 1234h
)?                    ## optional
\s*
(?:                   ## minutes
  (?P<min> \d+)+m     ## syntax: 1234m
)?                    ## optional
\s*
(?:                   ## seconds
  (?P<sec> \d+)+s?    ## syntax: 1234s or 1234
)?                    ## optional
$
'''

exactRe=re.compile(_exact, re.VERBOSE | re.MULTILINE | re.I)
addRe=re.compile(_add, re.VERBOSE | re.MULTILINE | re.I)

class TimeException(Exception): pass

def convert(s):
    s=s.strip()

    m=exactRe.match(s)
    if m:
        tm=time.time()
        year, mon, mday, hour, min, sec, wday, yday, isdst = time.localtime(tm)

        hour=int(m.group('hour'))
        min=int(m.group('min'))
        sec=int(m.group('sec') or '00')

        ret=time.mktime( (year, mon, mday, hour, min, sec, wday, yday, isdst) )

        while ret < tm:
            ret += 86400

        return ret

    m=addRe.match(s)
    if m:
        hour=int(m.group('hour') or '0')
        min=int(m.group('min') or '0')
        sec=int(m.group('sec') or '0')

        addSecs=hour*3600 + min*60 + sec

        return time.time()+addSecs

    raise TimeException('Invalid syntax')

if __name__=='__main__':
    year, mon, mday, hour, min, sec, wday, yday, isdst = time.localtime()
    print (hour, min, sec)
    print time.time()-time.mktime(time.localtime())
    
    print convert('11.23')-time.time()
    
