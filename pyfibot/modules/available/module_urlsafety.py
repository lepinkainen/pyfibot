from __future__ import unicode_literals, print_function, division
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import re


def handle_url(bot, user, channel, url, msg):
    s = requests.Session()
    s.get('http://www.unmaskparasites.com/token/')
    dt = datetime.utcnow()
    dt_str = '%i-%i-%i-%i-%i-%i' % (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    r = s.post('http://www.unmaskparasites.com/results/', {'siteUrl': url, 't': dt_str})
    bs = BeautifulSoup(r.text)
    try:
        span = bs.find('div', {'class': 'conclusion'}).find('span')
    except AttributeError:
        return
    state = span.text.replace('<', '').replace('>', '').strip()
    if state != 'clean':
        info = bs.find('div', {'class': 'brief_report'}).text.strip()
        info = re.sub(r'\(.*?\)', '', info).strip()

        # To remove as many false positives as possible,
        # there seems to be quite a lot of sites with one
        # suspicious inline script...
        if info == '1 suspicious inline script found.':
            return

        return bot.say(channel, 'Warning: Site seems to be %s! (%s)' % (state, info))
