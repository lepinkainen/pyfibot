#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Pyfibot START Knowledge Parser
@author Ville 'tuhoojabotti' Lahdenvuo <tuhoojabotti@gmail.com> (http://www.tuhoojabotti.com/)
@copyright Copyright (c) 2011 Ville Lahdenvuo
@licence BSD

"""

import urllib
import re
import htmlentitydefs
import sys
import os
import logging
import yaml

# Initialize logger
log = logging.getLogger("ask")

"""Config module_ask.conf:
sentences: 1      - How many sentences of the output to print if it's longer than max length
maxlength: 150    - How many chars is the max length of output
Note: A shortlink will be applied after the maxlength e.g. See http://href.fi/xxx for more.
"""


def init(botconfig):
    global askconfig
    # Read configuration
    configfile = os.path.join(sys.path[0], "modules", "module_ask.conf")
    askconfig = yaml.load(file(configfile))


def command_ask(bot, user, channel, args):
    """Ask a question from the START (http://start.csail.mit.edu/) Usage: .ask <question>"""
    # SPAM!
    return bot.say(channel, getSTARTReply(args))


def getSTARTReply(q):
    if len(q) < 3 or not q:
        return "Your argument is invalid."
    # Some variables
    sentences = askconfig.get("sentences", 1)
    absmaxlen = askconfig.get("maxlength", 120)
    url = "http://start.csail.mit.edu/startfarm.cgi?QUERY=%s" % urllib.quote_plus(q)
    # For parsing
    answers = []
    media = False  # Do we have media such as js, img in the results
    fails = re.compile(
        "(KNOW-DONT-KNOW|DONT-KNOW|UNKNOWN-WORD|MISSPELLED-WORD|CANT-PARSE|FORBIDDEN-ASSERTION|LEXICON)"
    )
    medias = re.compile("doctype|click|map|below", re.IGNORECASE)
    # Retrieve data from the internet service
    bs = getUrl(url).getBS()
    if not bs:
        return "Failed to contact START. Try again later."
    # Find useful tags from the HTML mess. (Those spans with no child spans with the quality T.)
    data_tags = [
        tag
        for tag in bs(name="span", attrs={"type": "reply", "quality": "T"})
        if len(tag(name="span", attrs={"type": "reply", "quality": "T"})) == 0
    ]

    if len(data_tags) == 0:
        # Find tags about the users fail
        fail_tags = [
            tag
            for tag in bs(name="span", attrs={"type": "reply", "quality": fails})
            if len(tag(name="span", attrs={"type": "reply", "quality": fails})) == 0
        ]

        if len(fail_tags) == 0:
            log.debug("Failed to parse data from:")
            log.debug(bs)
            log.debug("data: %s" % data_tags)
            log.debug("fails: %s" % fail_tags)
            return "Failed to parse data. :/"
        else:  # Let's return the fail tag then.
            s = "".join(
                [
                    tag
                    for tag in fail_tags[0](text=True)
                    if type(tag) != Comment and re.search("Accept|Abort", tag) is None
                ]
            )
            s = re.sub(
                "<.*?>", "", s
            )  # Remove possibly remaining HTML tags (like BASE) that aren't parsed by bs
            s = re.sub("\n|\r|\t|&nbsp;", " ", s).strip(" \t")  # One-line it.
            s = re.sub("[ ]{2,}", " ", s)  # Compress multiple spaces into one
            s = unescape(s)  # Clean up hex and html escaped chars
            if len(s) > absmaxlen:
                s = s[:absmaxlen].split(" ")
                s.pop()
                s = " ".join(s) + "..."
            return unicode("Fail: " + s).encode("utf-8")

    else:

        for answer in data_tags:

            # Cleanups on html depth
            [
                sup.replaceWith(("^%s" % sup.string) if sup.string is not None else " ")
                for sup in answer.findAll("sup")
            ]  # Handle <SUP> tags
            [br.replaceWith(" ") for br in answer.findAll("br")]  # Handle <BR> tags
            [
                td.extract()
                for td in answer.findAll("td")
                if len("".join(td.findAll(text=True))) < 10
            ]  # Handle <TABLE> data
            [
                cm.extract()
                for cm in answer.findAll(text=lambda text: isinstance(text, Comment))
            ]  # Handle <!-- Comments -->

            # Find media by looking for tags like img and script and words like doctype, map, click (It sometimes embeds a whole HTML-document to the results. :S)
            if (
                len(answer.findAll({"img": True, "script": True})) > 0
                or medias.search("".join(answer(text=True))) is not None
            ):
                media = True
            # Cleanups on string depth
            s = "".join(answer(text=True))
            s = re.sub(
                "<.*?>", "", s
            )  # Remove possibly remaining HMTL tags (like BASE) that aren't parsed by bs
            s = re.sub("\n|\r|\t|&nbsp;", " ", s).strip(" \t")  # One-line it.
            s = re.sub("[ ]{2,}", " ", s)  # Compress multiple spaces into one
            s = unescape(s)  # Clean up hex and html escaped chars

            answers.append(s)

        # Try to find suitable data for IRC
        try:
            answer = min(
                (ans for ans in answers if len(ans) > 10 and not medias.search(ans)),
                key=len,
            )
        except:
            if media is False:
                return "Sorry, I don't know"
            else:
                return "Take a look at %s :P" % shorturl(url).encode("utf-8")

        # Crop long answer...
        if len(answer) > absmaxlen:
            # It's longer than absolute max chars, try splitting first n sentences.
            answer = ". ".join(answer.split(". ")[:sentences]) + "."

            # It's still too long, so we'll split by word. :/
            if len(answer) > absmaxlen:
                answer = answer[:absmaxlen].split(" ")
                answer.pop()
                answer = " ".join(answer)

            answer = "%s &ndash; See %s for more." % (answer, shorturl(url))

        # It's not too long, but additional media is available, so let's give a link. :)
        elif media is True:
            answer = "%s &ndash; See %s for media." % (answer, shorturl(url))
        return unicode(unescape(answer)).encode("utf-8")


def unescape(text):
    """Unescape ugly wtf-8-hex-escaped chars"""

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
        return text  # leave as is

    return re.sub(r"&#?\w+;", fixup, text)


def shorturl(url):
    try:
        return urllib.urlopen(
            "http://href.fi/api.php?%s" % urllib.urlencode({"create": url})
        ).read()
    except:  # If something fails
        return url
