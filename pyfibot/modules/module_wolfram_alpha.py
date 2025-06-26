# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import urllib.parse as urllib
import logging
import re
import xml.etree.ElementTree as etree

log = logging.getLogger("wolfram_alpha")


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
    return clean_answer(_string)


def clean_answer(_string):
    if _string:
        res = re.sub(
            "[ ]{2,}",
            " ",
            _string.replace(" | ", ": ").replace("\n", " | ").replace("~~", " ≈ "),
        ).strip()
        res = res.replace(r"\:0e3f", "฿")
        res = res.replace(r"\:ffe5", "￥")
        return res


def command_wa(bot, user, channel, args):
    """Query Wolfram Alpha"""
    if not appid:
        log.warn("Appid not specified in configuration!")
        return False

    r = bot.get_url(query % (urllib.quote(args.encode("utf-8")), appid))

    if r.status_code != 200:
        return

    root = etree.fromstring(r.content)
    # Find all pods with plaintext answers
    # Filter out None -answers, strip strings and filter out the empty ones
    plain_text_pods = filter(
        None,
        [
            p.text.strip()
            for p in root.findall(".//subpod/plaintext")
            if p is not None and p.text is not None
        ],
    )

    # no answer pods found, check if there are didyoumeans-elements
    if not plain_text_pods:
        didyoumeans = root.find("didyoumeans")
        # no support for future stuff yet, TODO?
        if not didyoumeans:
            # If there's no pods, the question clearly wasn't understood
            return bot.say(channel, "Sorry, couldn't understand the question.")

        options = []
        for didyoumean in didyoumeans:
            options.append("'%s'" % didyoumean.text)
        line = " or ".join(options)
        line = "Did you mean %s?" % line
        return bot.say(channel, line.encode("UTF-8"))

    # If there's only one pod with text, it's probably the answer
    # example: "integral x²"
    if len(plain_text_pods) == 1:
        answer = clean_question(plain_text_pods[0])
        return bot.say(channel, answer)

    # If there's multiple pods, first is the question interpretation
    question = clean_question(plain_text_pods[0])
    # and second is the best answer
    answer = clean_answer(plain_text_pods[1])
    return bot.say(channel, "%s = %s" % (question, answer))
