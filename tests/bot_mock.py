import requests

from pyfibot import botcore


class BotMock(botcore.CoreCommands):
    config = {}

    def get_url(self, url, params={}, nocache=False, cookies=None):
        print("Getting url %s" % url)
        if cookies:
            return requests.get(url, params=params, cookies=cookies)
        return requests.get(url, params=params)

    def say(self, channel, message, length=None):
        #return("%s|%s" % (channel, message))
        return (channel, message)
