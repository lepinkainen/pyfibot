# -*- coding: utf-8 -*-

import re
from operator import pow, add, sub, mul, div, mod

import urllib2
import requests
import json


def doTheMath(matchobj):
    e = matchobj.groups()
    res = {"^": pow, "+": add, "-": sub, "*": mul, "/": div, "%": mod}[e[1]](
        float(e[0]), float(e[2])
    )
    return str(res)


def calc(str, match=True):
    if match:
        str = str.group(0)[1:-1]

    while True:
        newstr = re.sub(r"[(][-+*^%/\d.]*[)]", calc, str)
        if newstr == str:
            break
        else:
            str = newstr

    for op in [r"[\^]", "[*/%]", "[-+]"]:
        while True:
            newstr = re.sub(r"(\-?[\d.]+)(%s)(\-?[\d.]+)" % op, doTheMath, str)
            if newstr == str:
                break
            else:
                str = newstr

    return str


def calc_google(args):
    google_url = "http://www.google.com/search?hl=en&num=1&q=%s"
    search_url = google_url % urllib2.quote(args)

    request = urllib2.Request(search_url)
    request.add_header(
        "User-Agent",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.1.4) Gecko/20091016 Firefox/3.5.4",
    )

    opener = urllib2.build_opener()

    d = opener.open(request).read()

    m = re.search("calculator-40.gif[^>]+><td>[^<]+<td[^>]+><h2[^>]+><b>([^<]+)</b>", d)
    if m:
        res = m.group(1)
        # clean up
        res = res.replace("<font size=-2> </font>", " ")
        res = res.replace("<sup>", "^").replace("</sup>", "")
        res = res.replace("&#215;", "×")
        return res
    else:
        return "Invalid calculation"


def calc_google_ig(args):
    google_url = "http://www.google.com/ig/calculator?hl=en&q=%s"
    search_url = google_url % urllib2.quote(args)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.1.4) Gecko/20091016 Firefox/3.5.4"
    }
    r = requests.get(search_url, headers=headers)
    d = r.text
    d = (
        d.replace("lhs", '"lhs"', 1)
        .replace("rhs", '"rhs"', 1)
        .replace("error", '"error"', 1)
        .replace("icc", '"icc"', 1)
    )
    res = json.loads(d)
    if not res["error"]:
        result = "%s = %s" % (res["lhs"], res["rhs"])
        return result.encode("ascii", "ignore")
    else:
        return "Invalid calculation"


def command_calc(bot, user, channel, args):
    if not args:
        return
    return bot.say(channel, calc_google_ig(args))
