"""irc-gallery.net url parser & handler"""

import re
import urllib
from util.BeautifulSoup import BeautifulSoup

igURLre = re.compile(".*irc-galleria\.(fi|net)")

def handle_url(user, channel, url):
    # not from irc-gallery, skip
    if not igURLre.match(url): return

    bs = getUrl(url).getBS()
    
    if not bs: return
    
    agetag = bs.first(text="Syntynyt:")
    
    if not agetag: return
    
    age = agetag.next.next.next.next.next.next.string
    age = age.strip(" (v)")
    
    age = float(age)
    
    if age < 16: say(channel, "VAARA: Sakkolihaaa! (%.2fv)" % age)
