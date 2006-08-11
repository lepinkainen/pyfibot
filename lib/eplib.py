
"""A basic library for getting data out of epguides.com"""

import re, urllib, string, time, datetime
import ConfigParser, os.path, sys, md5

class Serie:
    """One serie"""
    
    def __init__(self, webname, name):
        self.name = name
        self.webname = webname
        self.checksum = None
        self.epdata = []

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "<%s (%d eps)>" % (self.name, len(self.epdata))

def getConfig(iniFileName="epwatcher.ini"):
    """Reads a config file of <name in epguides>=<display name> -pairs and returns it as a dict"""
    
    # read config with config parser
    cp = ConfigParser.RawConfigParser()
    # make keys case sensitive
    cp.optionxform = lambda x: str(x)

    # try to find the ini file
    cp.read([iniFileName, os.path.join(sys.path[0], iniFileName), os.path.join(sys.path[0], iniFileName)])

    series = {}

    # series to watch
    if cp.has_section('series'):
        for k,v in cp.items('series'):
            series[k] = v

    return series

def printSerieData(series, outputstring, daysbefore=1, daysafter=3):
    """Print serie data in a neat form to stdout

    @param seriedata Old serie data for initialization
    
    """
    now = time.gmtime()

    # datetime format for easy comparisons
    nowdate = datetime.date(now[0], now[1], now[2])
    yesterday = nowdate - datetime.timedelta(days=1)
    tomorrow = nowdate + datetime.timedelta(days=1)

    comingupseries = []

    # analyze
    for serie in series:
        for ep in serie.epdata:
            airdate = ep['airdate2']
            # create a timedelta object of the two dates
            # and compare to the given ranges
            td = airdate - nowdate
            if td.days < daysafter and td.days >= -daysbefore:
                comingupseries.append( (ep['airdate2'], serie.name, ep['season'], ep['episode'], ep['epname']) )

    # sort by first item (date)
    comingupseries.sort()

    # the output string needs some preformatting to handle long serie names
    outputstring = outputstring.replace("%(", "%%(")

    maxlen = 0

    for airdate, seriename, season, episode, epname in comingupseries:
        if len(seriename) > maxlen: maxlen = len(seriename)


    outputstring = outputstring % (-maxlen)

    # go through all the series which are on during the given timeframe
    for airdate, seriename, season, episode, epname in comingupseries:
        # format the airdate to a readable form
        if airdate == nowdate:
            airdate = "TODAY"
        elif airdate == yesterday:
            airdate = "YESTERDAY"
        elif airdate == tomorrow:
            airdate = "TOMORROW"
        else:
            airdate = airdate.strftime("%d.%m.%Y")

        # print the formatted string
        print outputstring % locals()

def getSerieData(serie, proxies=None, url="http://www.epguides.com/"):
    """Get all data for given series from epguides.com

    @param series a dict of {<name on epguides>:<long name>, ...}
    """
    
    # line example
    # 1.   1- 1       535J     30 Sep 01   <a href="http://www.tvtome.com/Alias/season1.html#ep1">Truth Be Told</a>
    epRe=re.compile("(?P<no>[\d]+)\.[\s]+(?P<season>[\d]+)-[ ]?(?P<episode>[\d]+)[\s]+(?P<prodno>[\w-]+)?[\s]+(?P<date>[\d]{1,2} [\w]{3} [\d]{2})[\s]+<[^>]+>(?P<name>.*)</a>")

    # set proxy here if needed
    f=urllib.urlopen("%s%s/" % (url, serie.webname), proxies=proxies)
    filedata=f.read()
    f.close()

    md5sum = md5.new(filedata).hexdigest()

    # no changes, don't update
    if serie.checksum == md5sum:
        return serie

    serie.checksum = md5sum
    
    # {<seriename> : [{epdata}, {epdata}, {epdata}], ...}
    
    tmp=filedata.split("\n")
    # if the file didn't split, try again
    # with a different separator
    if int(len(tmp)) == 1:
        tmp=filedata.split("\r")
    filedata=tmp

    # remove leading and trailing spaces
    filedata=map(string.strip, filedata)

    # remove old data
    serie.epdata = []

    for line in filedata:
        ###
        # find episodes
        ###
        m = epRe.match(line)
        if m:
            
            # convert datestring to gmtime format
            t = time.strptime(m.group('date'), '%d %b %y')
            
            # put episode data into a nifty dict
            data = {'epno'    : m.group('no'),
                    'season'  : int(m.group('season')),
                    'episode' : int(m.group('episode')),
                    'prodno'  : m.group('prodno'),
                    'airdate' : m.group('date'),
                    'airdate2': datetime.date(t[0], t[1], t[2]),
                    'epname'  : m.group('name')}
        
            serie.epdata.append(data)

        
    return serie
