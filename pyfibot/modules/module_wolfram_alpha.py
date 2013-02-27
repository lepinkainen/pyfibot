from __future__ import unicode_literals, print_function, division
import urllib
import logging

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


def command_wa(bot, user, channel, args):
    """Query Wolfram Alpha"""
    if not appid:
        log.warn("Appid not specified in configuration!")
        return

    r = bot.get_url(query % (urllib.quote(args), appid))

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

    # first pod has the question as WA sees it
    question = pods[0].xpath("subpod/plaintext")[0].text
    # second one has the best answer
    answer = pods[1].xpath("subpod/plaintext")[0].text

    line = "%s: %s" % (question, answer)
    return bot.say(channel, line.encode("UTF-8"))
