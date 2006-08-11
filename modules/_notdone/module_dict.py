"""English-Finnish-English dictionary search"""

import re
from urllib import urlencode

def command_dict(user, channel, args):
    """Search from http://efe.scape.net and return first 10 results"""
    if not args: return
    keyword = args
    
    # fetch page
    urlitem = getUrl("http://efe.scape.net/index.php?criteria=%s&page=1" % keyword)
    bs = urlitem.getBS()
    content = urlitem.getContent()
    
    if content.find("No results were found") > -1:
        say(channel, "No results were found")
    
    # parse results
    keys = bs.fetch('td', {'nowrap': 'nowrap'}, text=re.compile('^\&nbsp;\&nbsp;[^&]'))
    defs = bs.fetch('td', {'nowrap': 'nowrap'}, text=re.compile('^\&nbsp;[^&]'))
    total = bs.fetch('td', {'colspan': '3', 'bgcolor': "#EEEEEE"})[0].contents[0]
    
    r = {}
    for x,y in zip(keys, defs):
        x = x.replace('&nbsp;','')
        r.setdefault(x, [])
        r[x].append(y.replace('&nbsp;',''))
    r = ["%s: [%s]" % (x, ', '.join(y)) for x,y in r.items()]
    print r
    
    # print results
    say(channel, total)
    say(channel, ', '.join(r))
    
if __name__ == '__main__':
    def say(c, m):
        print m
    
    def getUrl(url):
        import urllib
        from BeautifulSoup import BeautifulSoup as soup
        feed = urllib.urlopen(url).read()
        return soup(feed), '', feed,
    
    command_dict('','', 'foo*')
