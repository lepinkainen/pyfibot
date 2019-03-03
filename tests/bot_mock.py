import os.path
import yaml
import logging

import requests
from pyfibot import pyfibot
from pyfibot import botcore

log = logging.getLogger("bot_mock")


class BotMock(botcore.CoreCommands):
    config = {}

    def __init__(self, config={}, network=None):
        self.config = config
        if network:
            self.network = network
            self.nickname = self.network.nickname
            self.lineRate = self.network.linerate
            self.password = self.network.password

    def get_url(self, url, nocache=False, params=None, headers=None, cookies=None):
        print("Getting url %s" % url)

        browser = (
            "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:43.0) Gecko/20100101 Firefox/43.0"
        )
        # Common session for all requests
        s = requests.session()
        s.stream = True  # Don't fetch content unless asked
        s.headers.update({"User-Agent": browser})
        # Custom headers from requester
        if headers:
            s.headers.update(headers)
        # Custom cookies from requester
        if cookies:
            s.cookies.update(cookies)

        try:
            r = s.get(url, params=params)
        except requests.exceptions.InvalidSchema:
            print("[ERROR] Invalid schema in URI: %s" % url)
            return None
        except requests.exceptions.ConnectionError:
            print("[ERROR] Connection error when connecting to %s" % url)
            return None

        size = int(r.headers.get("Content-Length", 0)) // 1024
        # log.debug("Content-Length: %dkB" % size)
        if size > 2048:
            print("[WARNING] Content too large, will not fetch: %skB %s" % (size, url))
            return None

        return r

    def say(self, channel, message, length=None):
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
                    _string = _string.decode("utf-8")
                except:
                    _string = _string.decode("iso-8859-1")
        return _string


class FactoryMock(pyfibot.PyFiBotFactory):
    protocol = BotMock

    def __init__(self, config={}):
        # run with main bot config if one exists
        main_config = os.path.join(os.path.dirname(__file__), "..", "config.yml")
        test_config = os.path.join(os.path.dirname(__file__), "test_config.yml")

        if not config or config == {}:
            if os.path.exists(main_config):
                log.debug("USING MAIN CONFIG")
                config = yaml.load(file(main_config))
            else:
                log.debug("USING TEST CONFIG")
                config = yaml.load(file(test_config))

        pyfibot.PyFiBotFactory.__init__(self, config)
        self.createNetwork(
            ("localhost", 6667), "nerv", "pyfibot", ["#pyfibot"], 0.5, None, False
        )
        self.createNetwork(
            ("localhost", 6667), "localhost", "pyfibot", ["#pyfibot"], 0.5, None, False
        )
        self.startFactory()
        self.buildProtocol(None)

    def startFactory(self):
        self.moduledir = "./pyfibot/modules/"
        self.allBots = {}

    def buildProtocol(self, address):
        # Go through all defined networks
        for network, server in self.data["networks"].items():
            p = self.protocol(network=server)
            self.allBots[server.alias] = p
            p.factory = self
