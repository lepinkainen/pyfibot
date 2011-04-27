#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Pyfibot START Knowledge Parser Module
@author Ville 'tuhoojabotti' Lahdenvuo <tuhoojabotti@gmail.com> (http://www.tuhoojabotti.com/)
@copyright Copyright (c) 2011 Ville Lahdenvuo
@licence BSD
"""

from util.BeautifulSoup import BeautifulStoneSoup, Comment
import sys, os, re, yaml, urllib, logging
import htmlentitydefs # for unescape()

log = logging.getLogger('ask') # Initialize logger

# Config module_ask.conf:
#  sentences: 1      - How many sentences of the output to print if it's longer than max length
#  maxlength: 120    - How many chars is the max length of output
# Note: A shortlink will be applied after the maxlength e.g. See http://href.fi/xxx for more.

def init(botconfig):
    global askconfig
    # Read configuration
    configfile = os.path.join(sys.path[0], 'modules', 'module_ask.conf')
    if os.path.exists(configfile):
        askconfig = yaml.load(file(configfile))
    else:
        log.warning("Config file 'module_ask.conf' missing, using default values.")
        askconfig = yaml.load("maxlength: 120\nsentences: 1")

def command_ask(bot, user, channel, args):
    """Ask a question from the START. (http://start.csail.mit.edu/) Usage: .ask <question>"""
    return bot.say(channel, getSTARTreply(args)) # SPAM!

def getSTARTreply(q):
    """Returns a string of data, hopefully answering the question in the parameter q."""
    if len(q)<3 or not q: return "Your argument is invalid."

    sentences = askconfig.get('sentences', 1)
    absmaxlen = askconfig.get('maxlength', 120)
    url       = "http://start.csail.mit.edu/startfarm.cgi?query=%s" % urllib.quote_plus(q)

    media     = False # Do we have media such as js or images in the results
    fails     = re.compile("((KNOW-DONT|DONT)-KNOW|(UNKNOWN|MISSPELLED)-WORD|" +
                           "CANT-PARSE|FORBIDDEN-ASSERTION|LEXICON)")
    medias    = re.compile("\b(doctype|click|map|below)\b", re.IGNORECASE)
    answers   = []

    # Retrieve data from the internet
    bs = getUrl(url).getBS()
    if not bs: return "Failed to contact START. Try again later."

    # Find useful tags from the HTML mess. (Those spans with no child spans with the quality T.)
    data_tags = [tag for tag in bs(name = "span", attrs = {'type':'reply','quality':'T'})
                        if not tag(name = "span", attrs = {'type':'reply','quality':'T'})]

    if not data_tags:
        # Find tags about the users fail
        fail_tags = [tag for tag in bs(name = "span", attrs = {'type':'reply','quality':fails})
                            if not tag(name = "span", attrs = {'type':'reply','quality':fails})]
        if not fail_tags:
            log.debug("Failed to parse data from:")
            log.debug(bs)
            log.debug("data: %s" % data_tags)
            log.debug("fails: %s" % fail_tags)
            return "Failed to parse data."
        else: # Let's return the fail tag then.
            s = "".join([ tag for tag in fail_tags[0](text=True)
                if type(tag) != Comment and re.search("Accept|Abort",tag) == None ])
            s = re.sub("<.*?>", "", s)                          # Remove possibly remaining HTML
            s = re.sub("\n|\r|\t|&nbsp;", " ", s).strip(' \t')  # One-line it.
            s = re.sub("[ ]{2,}", " ", s)                       # Compress multiple spaces into one
            if len(s)>absmaxlen:
                s = s[:absmaxlen].split(' ')
                s.pop()
                s = " ".join(s) + "&hellip;"
            return unicode(unescape(s)).encode('utf-8')
    else:
        for answer in data_tags:
            # Cleanups on HTML depth: SUP, BR, TD and COMMENTS
            [sup.replaceWith( ("^%s" % sup.string) if sup.string != None else " " )
                for sup in answer.findAll('sup')]
            [br.replaceWith(" ") for br in answer.findAll('br')]
            [td.extract() for td in answer.findAll('td') if len( "".join(td.findAll(text=True)) ) < 10]
            [cm.extract() for cm in answer.findAll(text=lambda text:isinstance(text, Comment))]

            # Find media by looking for tags like img and script and some keywords
            if (answer.findAll({"img": True,"script": True}) or
                medias.search( "".join(answer(text=True)) ) is not None): media = True

            # Cleanups on string depth
            s = "".join(answer(text=True))
            s = re.sub("<.*?>", "", s)                          # Remove possibly remaining HMTL
            s = re.sub("\n|\r|\t|&nbsp;", " ", s).strip(' \t')  # One-line it.
            s = re.sub("[ ]{2,}", " ", s)                       # Compress multiple spaces into one
            s = unescape(s)                                     # Clean up hex and html escaped chars

            answers.append(s)

        # Try to find suitable data for IRC
        try:
            answer = min( (ans for ans in answers if len(ans) > 10 and not medias.search(ans)), key=len )
        except:
            if media == False:
                return "Sorry, I don't know"
            else:
                return "Take a look at %s" % shorturl(url).encode("utf-8")

        # Crop long answer...
        if len(answer) > absmaxlen:
            # It's longer than absolute max chars, try splitting first n sentences.
            answer = ". ".join(answer.split(". ")[:sentences])+"."

            # It's still too long, so we'll split by word. :/
            if len(answer) > absmaxlen:
                answer = answer[:absmaxlen].split(" ")
                answer.pop() # plops
                answer = " ".join(answer) + "&hellip;"

            answer = "%s &ndash; %s" % (answer, shorturl(url))
        # Additional media is available, so let's give a link. :)
        elif media: answer = "%s &ndash; %s" % (answer, shorturl(url))

        return unicode(unescape(answer)).encode('utf-8')

# -= HELPERS =- #

def unescape(text):
    """Unescapes ugly wtf-8-escaped chars from text"""
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

def shorturl(url):
    """Create href.fi shorturl"""
    try:
        return urllib.urlopen("http://href.fi/api.php?%s" % urllib.urlencode({'create': url})).read()
    except: # If something fails
        return url
