import requests

from pyfibot import botcore


class BotMock(botcore.CoreCommands):
    config = {}

    def __init__(self, config={}):
        self.config = config

    def get_url(self, url, params={}, nocache=False, cookies=None):
        print("Getting url %s" % url)
        if cookies:
            return requests.get(url, params=params, cookies=cookies)
        return requests.get(url, params=params)

    def say(self, channel, message, length=None):
        #return("%s|%s" % (channel, message))
        return (channel, message)

    def to_utf8(self, _string):
        """Convert string to UTF-8 if it is unicode"""
        if isinstance(_string, unicode):
            _string = _string.encode("UTF-8")
        return _string

    def to_unicode(self, _string):
        """Convert string to UTF-8 if it is unicode"""
        if not isinstance(_string, unicode):
            try:
                _string = unicode(_string)
            except:
                try:
                    _string = _string.decode('utf-8')
                except:
                    _string = _string.decode('iso-8859-1')
        return _string
