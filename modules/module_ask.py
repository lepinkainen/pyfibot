# -*- coding: utf-8 -*-

""" START Knowledge Parser by tuhoojabotti (http://www.tuhoojabotti.com/) """

import urllib, re, htmlentitydefs
from util.BeautifulSoup import BeautifulStoneSoup

def command_ask(bot, user, channel, args):
    """Asks a question from the START (http://start.csail.mit.edu/) Usage: .ask <question>"""

    # Config
    sentences = 1
    absmaxlen = 200

    # Retrieve data!
    if len(args)<3 or not args: return bot.say(channel, "Your argument is invalid.")
    args = urllib.quote_plus(args)
    bs = getUrl("http://start.csail.mit.edu/startfarm.cgi?QUERY=%s" % args).getBS()
    if not bs: return

    # Try parsing something usefull out of it.
    elems = bs(name="span",attrs={'quality' : re.compile("(T|KNOW-DONT-KNOW|DONT-KNOW|UNKNOWN-WORD)")})
    answer = ""
    for elem in elems:
        # If it has no child spans, it's the one we want!
        if len(elem.findAll(name="span",attrs={'quality' : re.compile("(T|KNOW-DONT-KNOW|DONT-KNOW|UNKNOWN-WORD)")}))==0:
            # Sup tags need some special treatment (mainly prepend ^ to their contents)
            for sup in elem.findAll('sup'):
                if sup.string != None: sup.replaceWith("^"+sup.string)
            # Parse together a reply.
            answer = "".join(elem.findAll(text=True)[2:]).strip()

    # Clean it up a bit...
    answer = re.sub("\n|\r|\t", " ", answer)    # One-line it.
    answer = re.sub("\[.*?\]|<.*?/>", "", answer)      # Remove cites and nasty html
    answer = re.sub("[ ]{2,}", " ", answer)     # Compress multiple spaces into one
    if not answer: return bot.say(channel, "Sorry, I don't know.") # See if there is an answer left. :P

    # Crop long answers...
    if len(answer) > 2000:
        answer = "Answer is too long, see %s for more information." % shorturl("http://start.csail.mit.edu/startfarm.cgi?QUERY=%s" % args)
    if len(answer) > absmaxlen:
        # It's longer than 390 chars, try splitting first 4 sentences.
        answer = ". ".join(answer.split(". ")[:sentences])+". &ndash; &ndash; %s" % shorturl("http://start.csail.mit.edu/startfarm.cgi?QUERY=%s" % args)
        # It's still too long, so we'll split by word. :/
        if len(answer) > absmaxlen:
            answer = answer[:absmaxlen].split(" ")
            answer.pop() # Last word is probably incomplete so get rid of it.
            answer = " ".join(answer)+" &ndash; &ndash; %s" % shorturl("http://start.csail.mit.edu/startfarm.cgi?QUERY=%s" % args)

    # Let's make it twisted safe
    answer = unescape(answer)       # Clean up hex escaped chars
    answer = unicode(answer)
    answer = answer.encode("utf-8") # WTF-8 <3
    # SPAM!
    return bot.say(channel, "%s" % answer)

# HELPERS

def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)


def shorturl(url): return getUrl("http://href.fi/api.php?create=%s" % url).getContent()
