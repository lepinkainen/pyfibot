# -*- coding: utf-8 -*-

""" START Knowledge Parser by tuhoojabotti (http://www.tuhoojabotti.com/) """

import urllib, re, htmlentitydefs, sys
from util.BeautifulSoup import BeautifulStoneSoup

def command_ask(bot, user, channel, args):
    """Asks a question from the START (http://start.csail.mit.edu/) Usage: .ask <question>"""
    # Config: If answer is longer than absmaxlen, then crop n sentences from the start, if still too long, crop to absmaxlenght and cut the last word
    # Note: A shortlink will be applied after the absmaxlen: See http://href.fi/xxx for more.
    sentences = 1
    absmaxlen = 150

    # Retrieve data!
    if len(args)<3 or not args: return bot.say(channel, "Your argument is invalid.")
    args = urllib.quote_plus(args)
    bs = getUrl("http://start.csail.mit.edu/startfarm.cgi?QUERY=%s" % args).getBS()
    if not bs: return

    # Try parsing something usefull out of it.
    elems = bs(name="span",attrs={'quality' : re.compile("(T|KNOW-DONT-KNOW|DONT-KNOW|UNKNOWN-WORD)")})
    answers = []
    data = False
    for elem in elems:
        # If it has no child spans, it's a one we want!
        if len(elem.findAll(name="span",attrs={'quality' : re.compile("(T|KNOW-DONT-KNOW|DONT-KNOW|UNKNOWN-WORD)")}))==0:
            # Handle <SUP>
            try:
                [sup.replaceWith(("^%s" % sup.string) if sup.string != None else " ") for sup in elem.findAll('sup')]
            except:
                print "sup fail!",sys.exc_info()[0]
            # Handle <TABLE> data
            try:
                for td in elem.findAll('td'):
                    # Remove tds if not text or too short, ugly table data. :/
                    if td.string != None:
                        if len(td.string)<10: td.extract()
                    else:
                        td.extract()
            except:
                print "td fail!",sys.exc_info()[0]
            # Parse together a reply.
            try:
                answers.append("".join(elem.findAll(text=True)[2:]))
            except:
                print "Error in parsing answer",sys.exc_info()[0]

    # Remove too short answers
    if len(answers)>0:
       data = True # We got some data.
    else:
       return bot.say(channel, "Sorry, I don't know.")
    try: # Try to find suitable data for IRC
        answer = min((ans for ans in answers if len(ans) > 35 and len(ans) < 2000), key=len)
    except:
        return bot.say(channel, "Sorry, I don't know")

    # Clean it up a bit...
    answer = re.sub("\[.*?\]|<.*?/>", "", answer)           # Remove cites and nasty html
    answer = re.sub("\n|\r|\t", " ", answer).strip(' \t')   # One-line it.
    answer = re.sub("[ ]{2,}", " ", answer)                 # Compress multiple spaces into one
    if not answer and not data:
        return bot.say(channel, "Sorry, I don't know.")     # See if there is an answer left. :P
    elif not answer and data:
        return bot.say(channel, "Found some data. See %s for details." % shorturl("http://start.csail.mit.edu/startfarm.cgi?QUERY=%s" % args))
    
    # Crop long answer...
    if len(answer) > absmaxlen:
        # It's longer than absolute max chars, try splitting first n sentences.
        answer = ". ".join(answer.split(". ")[:sentences])+"." # %s" % shorturl("http://start.csail.mit.edu/startfarm.cgi?QUERY=%s" % args)
        # It's still too long, so we'll split by word. :/
        if len(answer) > absmaxlen:
            answer = answer[:absmaxlen].split(" ")
            answer.pop() # Last word is probably incomplete so get rid of it.
            answer = " ".join(answer) # %s" % shorturl("http://start.csail.mit.edu/startfarm.cgi?QUERY=%s" % args)
        answer = "%s &ndash; See %s for more." % (answer, shorturl("http://start.csail.mit.edu/startfarm.cgi?QUERY=%s" % args))

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

def shorturl(url): # Get and href.fi shorted url
    try: 
        return getUrl("http://href.fi/api.php?create=%s" % url).getContent()
    except: # Failed!
        return url
