#!/usr/bin/python
# -*- coding: iso8859-1 -*-

"""
Description of software

@author Riku 'Shrike' Lindblad (shrike@addiktit.net)
@copyright Copyright (c) 2004 Riku Lindblad
@license GPL
"""

__date__ = "$Date: 2004/04/06 10:07:05 $"
__version__ = "$Revision: 1.1 $"

import urllib, re
from sgmllib import SGMLParser

class tiesaaParser(SGMLParser):

    """Get weather from Tielaitos"""

    def __init__(self):
        self.go = False

        self.data = []

        self.tmpdata = []
                
        #SGMLParser.reset(self)
        SGMLParser.reset(self)
        SGMLParser.__init__(self)
        
    def start_table(self, attrs):
        if attrs == [('border', '0')]:
            self.go = True

    def end_table(self):
        self.go = False

    def handle_data(self, text):
        if self.go:
            text = text.strip()
            if text.startswith('Tie '):
                self.data.append(self.tmpdata)
                self.tmpdata = []
            if len(text) != 0:
                self.tmpdata.append(text)
    
    def getData(self):
        return self.data[1:]

    def error(self, error):
        pass

def getWeatherdata():
    urls = []
    for i in range(1,23):
        urls.append('http://www.tiehallinto.fi/alk/tiesaa/tiesaa_maak_%d.html' % i)

    tp = tiesaaParser()

    weatherdata = []
    
    for url in urls:
        f = urllib.urlopen(url)
        data = f.read()
        f.close()

        tp.feed(data)

        weatherdata.append(tp.getData())

    return weatherdata

def getWeather(station):
    weatherdata = getWeatherdata()

    sRegex = re.compile('%s' % station, re.I)
    
    for region in weatherdata:
        for location in region:
            if sRegex.search(location[0]):
                l = location
                # Mikkeli, Läsänkoski, mitattu klo 12:03: 7.2°C, poutaa. Tien lämpötila 14.9°C, tien pinta kuiva.
                print "%s, mitattu klo %s: %s°C, %s. Tien lämpötila %s°C, tien pinta %s." % (l[0], l[1], l[2], l[4], l[3], l[5])
            else:
                print location[0]
    print "Weather data for %s not found" % station
                
def main():
    getWeather("espoo")
            
# Main part of code
if __name__ == '__main__':
    main()
