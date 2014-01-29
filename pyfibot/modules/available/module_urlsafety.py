from __future__ import unicode_literals, print_function, division
import requests
from datetime import datetime
from bs4 import BeautifulSoup


def handle_url(bot, user, channel, url, msg):
    s = requests.Session()
    s.get('http://www.unmaskparasites.com/token/')
    dt = datetime.utcnow()
    dt_str = '%i-%i-%i-%i-%i-%i' % (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    r = s.post('http://www.unmaskparasites.com/results/', {'siteUrl': url, 't': dt_str})
    bs = BeautifulSoup(r.text)
    state = bs.find('div', {'class': 'conclusion'}).find('span')['class'][0].strip()
    if state != 'clean':
        return bot.say(channel, 'Warning: Site seems to be %s!' % state)
