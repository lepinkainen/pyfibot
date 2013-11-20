# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import urllib
import logging
import re

log = logging.getLogger('wolfram_alpha')

try:
    from lxml import etree
    log.debug("running with lxml.etree")
except ImportError:
    log.debug("module_wolfram_alpha requires lxml.etree for xpath support")

appid = None
query = "http://api.wolframalpha.com/v2/query?input=%s&appid=%s"


def init(bot):
    global appid
    config = bot.config.get("module_wolfram_alpha", {})
    appid = config.get("appid", "")
    if appid:
        log.info("Using Wolfram Alpha appid %s" % appid)
    else:
        log.warning("Appid not found from config!")


def clean_question(_string):
    if _string:
        return re.sub("[ ]{2,}", " ", _string.replace(' | ', ' ').replace('\n', ' ').replace('~~', ' ≈ ')).strip()


def clean_answer(_string):
    if _string:
        return re.sub("[ ]{2,}", " ", _string.replace(' | ', ': ').replace('\n', ' | ').replace('~~', ' ≈ ')).strip()


def command_wa(bot, user, channel, args):
    """Query Wolfram Alpha"""
    if not appid:
        log.warn("Appid not specified in configuration!")
        return False

    r = bot.get_url(query % (urllib.quote(args.encode('utf-8')), appid))

    if r.status_code != 200:
        return

    root = etree.fromstring(r.content)
    # find all pods
    pods = root.findall("pod")

    # no answer pods found, check if there are didyoumeans-elements
    if not pods:
        didyoumeans = root.find("didyoumeans")
        # no support for future stuff yet, TODO?
        if not didyoumeans:
            return

        options = []
        for didyoumean in didyoumeans:
            options.append("'%s'" % didyoumean.text)
        line = " or ".join(options)
        line = "Did you mean %s?" % line
        return bot.say(channel, line.encode("UTF-8"))

    # Question interpretations are in text format in subpods/plaintext
    # find all these and filter empty values
    pods_as_text = filter(None, [p.xpath('subpod/plaintext')[0].text for p in pods])

    # If there's no pods, the question clearly wasn't understood
    if not pods_as_text:
        return bot.say(channel, "Sorry, couldn't understand the question.")

    # If there's only one pod with text, it's probably the answer
    # example: "integral x²"
    if len(pods_as_text) == 1:
        answer = clean_question(pods_as_text[0])
        return bot.say(channel, answer)

    # If there's multiple pods, first is the question interpretation
    question = clean_question(pods_as_text[0].replace(' | ', ' ').replace('\n', ' '))
    # and second is the best answer
    answer = clean_answer(pods_as_text[1])
    return bot.say(channel, '%s = %s' % (question, answer))
