import requests
from pyfibot import pyfibot
from pyfibot import botcore


class BotMock(botcore.CoreCommands):
    config = {}

    def __init__(self, config={}, network=None):
        self.config = config
        if network:
            self.network = network
            self.nickname = self.network.nickname
            self.lineRate = self.network.linerate
            self.password = self.network.password

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


class FactoryMock(pyfibot.PyFiBotFactory):
    protocol = BotMock

    def __init__(self, config={}):
        pyfibot.PyFiBotFactory.__init__(self, config)
        self.createNetwork(('localhost', 6667), 'nerv', 'pyfibot', ['#pyfibot'], 0.5, None, False)
        self.createNetwork(('localhost', 6667), 'localhost', 'pyfibot', ['#pyfibot'], 0.5, None, False)
        self.startFactory()
        self.buildProtocol(None)

    def startFactory(self):
        self.moduledir = './pyfibot/modules/'
        self.allBots = {}

    def buildProtocol(self, address):
        # Go through all defined networks
        for network, server in self.data['networks'].items():
            p = self.protocol(network=server)
            self.allBots[server.alias] = p
            p.factory = self
