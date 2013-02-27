#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A modular python bot based on the twisted matrix irc library

@author Riku 'Shrike' Lindblad (shrike@addiktit.net)
@copyright Copyright (c) 2006 Riku Lindblad
@license New-Style BSD
"""

from __future__ import print_function, division
import sys
import os.path
import time
import requests
import fnmatch
import logging
import logging.handlers
import json
import jsonschema

# Make requests quieter by default
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)

try:
    import yaml
except ImportError:
    print("PyYAML not found, please install from http://pyyaml.org/wiki/PyYAML")
    sys.exit(1)

# twisted imports
try:
    from twisted.internet import reactor, protocol, ssl
except ImportError:
    print("Twisted library not found, please install Twisted from http://twistedmatrix.com/products/download")
    sys.exit(1)

# default timeout for socket connections
import socket
socket.setdefaulttimeout(20)

import botcore

log = logging.getLogger('core')


class Network:
    """Represents an IRC network"""
    def __init__(self, root, alias, address, nickname, channels=None, linerate=None, password=None, is_ssl=False):
        self.root = root
        self.alias = alias                         # network name
        self.address = address                     # server address
        self.nickname = nickname                   # nick to use
        self.channels = channels or {}             # channels to join
        self.linerate = linerate
        self.password = password
        self.is_ssl = is_ssl

    def __repr__(self):
        return 'Network(%r, %r)' % (self.alias, self.address)


class InstantDisconnectProtocol(protocol.Protocol):
    def connectionMade(self):
        self.transport.loseConnection()


class ThrottledClientFactory(protocol.ClientFactory):
    """Client factory that inserts a slight delay to connecting and reconnecting"""
    lostDelay = 10
    failedDelay = 60

    def clientConnectionLost(self, connector, reason):
        print(connector.getDestination())
        log.info("connection lost (%s): reconnecting in %d seconds" % (reason, self.lostDelay))
        reactor.callLater(self.lostDelay, connector.connect)

    def clientConnectionFailed(self, connector, reason):
        log.info("connection failed (%s): reconnecting in %d seconds" % (reason, self.failedDelay))
        reactor.callLater(self.failedDelay, connector.connect)


class PyFiBotFactory(ThrottledClientFactory):
    """python.fi bot factory"""

    version = "2013-02-19"
    protocol = botcore.PyFiBot
    allBots = None
    moduledir = os.path.join(sys.path[0], "modules/")
    startTime = None
    config = None

    def __init__(self, config):
        """Initialize the factory"""
        self.config = config
        self.data = {}
        self.data['networks'] = {}
        self.ns = {}
        # Cache url contents for 5 minutes, check for old entries every minute
        #self._urlcache = timeoutdict.TimeoutDict(timeout=300, pollinterval=60)

    def startFactory(self):
        self.allBots = {}
        self.starttime = time.time()
        self._loadmodules()
        ThrottledClientFactory.startFactory(self)
        log.info("factory started")

    def stopFactory(self):
        del self.allBots
        ThrottledClientFactory.stopFactory(self)
        log.info("factory stopped")

    def buildProtocol(self, address):
        # we are connecting to a server, don't know which yet
        log.info("Building protocol for %s", address)

        # Go through all defined networks
        for network, server in self.data['networks'].items():
            log.debug("Looking for matching network: %s - %s", server, address)
            # get all of the ipv4 and ipv6 addresses configured for this domain name
            addrinfo = socket.getaddrinfo(server.address[0], server.address[1])
            ips = set()
            for ip in addrinfo:
                ips.add(ip[4][0])  # (2, 1, 6, '', ('192.168.191.241', 6667))

            # if the address we are connecting to matches one of the IPs defined for
            # this network, connect to it and stop looking
            if address.host in ips:
                log.debug("Connecting to %s / %s", server, address)
                p = self.protocol(server)
                self.allBots[server.alias] = p
                p.factory = self
                return p

        # TODO: Remove this handling altogether
        log.debug("Fall back to old process...")
        fqdn = socket.getfqdn(address.host)
        log.debug("Address: %s - %s", address, fqdn)

        # Fallback to the old, stupid, way of connecting
        for network, server in self.data['networks'].items():
            log.debug("Looking for matching network: %s - %s", server, fqdn)
            found = False
            if server.address[0] == fqdn:
                log.debug("fqdn matches server address")
                found = True
            if server.address[0] == address.host:
                log.debug("host matches server address")
                found = True
            if found:
                log.debug("Connecting to %s / %s", server, address)
                p = self.protocol(server)
                self.allBots[server.alias] = p
                p.factory = self
                return p

        # No address found
        log.error("Unknown network address: " + repr(address))
        return InstantDisconnectProtocol()

    def createNetwork(self, address, alias, nickname, channels=None, linerate=None, password=None, is_ssl=False):
        self.setNetwork(Network("data", alias, address, nickname, channels, linerate, password, is_ssl))

    def setNetwork(self, net):
        nets = self.data['networks']
        nets[net.alias] = net
        self.data['networks'] = nets

    def clientConnectionLost(self, connector, reason):
        """Connection lost for some reason"""
        log.info("connection to %s lost: %s" % (str(connector.getDestination().host), reason))

        # find bot that connects to the address that just disconnected
        for n in self.data['networks'].values():
            dest = connector.getDestination()
            if (dest.host, dest.port) == n.address:
                if n.alias in self.allBots:
                    # did we quit intentionally?
                    if not self.allBots[n.alias].hasQuit:
                        # nope, reconnect
                        ThrottledClientFactory.clientConnectionLost(self, connector, reason)
                    del self.allBots[n.alias]
                    return
                else:
                    log.info("No active connection to known network %s" % n.address[0])

    def _finalize_modules(self):
        """Call all module finalizers"""
        for module in self._findmodules():
            # if rehashing (module already in namespace), finalize the old instance first
            if module in self.ns:
                if 'finalize' in self.ns[module][0]:
                    log.info("finalize - %s" % module)
                    self.ns[module][0]['finalize']()

    def _loadmodules(self):
        """Load all modules"""
        self._finalize_modules()
        for module in self._findmodules():
            env = self._getGlobals()
            log.info("load module - %s" % module)
            # Load new version of the module
            execfile(os.path.join(self.moduledir, module), env, env)
            # Initialize module
            if 'init' in env:
                log.info("initialize module - %s" % module)
                env['init'](self)
            # Add to namespace so we can find it later
            self.ns[module] = (env, env)

    def _findmodules(self):
        """Find all modules"""
        modules = [m for m in os.listdir(self.moduledir) if m.startswith("module_") and m.endswith(".py")]
        return modules

    def _getGlobals(self):
        """Global methods for modules"""
        g = {}

        g['getUrl'] = self.get_url
        g['get_url'] = self.get_url
        g['getNick'] = self.getNick
        g['isAdmin'] = self.isAdmin
        return g

    def get_url(self, url, nocache=False, params=None, headers=None):
        return self.getUrl(url, nocache, params, headers)

    def getUrl(self, url, nocache=False, params=None, headers=None):
        """Gets data, bs and headers for the given url, using the internal cache if necessary"""

        # TODO: Make this configurable in the config
        browser = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.95 Safari/537.11"

        # Common session for all requests
        s = requests.session()
        s.verify = False
        s.stream = True  # Don't fetch content unless asked
        s.headers.update({'User-Agent':browser})
        # Custom headers from requester
        if headers:
            s.headers.update(headers)

        r = s.get(url, params=params)

        size = int(r.headers.get('Content-Length', 0)) // 1024
        #log.debug("Content-Length: %dkB" % size)
        if size > 2048:
            log.warn("Content too large, will not fetch: %skB %s" % (size, url))
            return None

        return r

    def getNick(self, user):
        """Parses nick from nick!user@host
        @type user: string
        @param user: nick!user@host
        @return: nick"""
        return user.split('!', 1)[0]

    def isAdmin(self, user):
        """Check if an user has admin privileges.
        @return: True or False"""
        for pattern in self.config['admins']:
            if fnmatch.fnmatch(user, pattern):
                return True
        return False


def init_logging(config):
    filename = os.path.join(sys.path[0], 'pyfibot.log')

    # get root logger
    logger = logging.getLogger()

    if False:
        handler = logging.handlers.RotatingFileHandler(filename, maxBytes=5000 * 1024, backupCount=20)
    else:
        handler = logging.StreamHandler()

    formatter = logging.Formatter('%(asctime)-15s %(levelname)-8s %(name)-11s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    if config.get('debug', False):
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)


def validate_config(config, schema):
    print("Validating configuration")
    v = jsonschema.Draft3Validator(schema)
    if not v.is_valid(config):
        print("Error(s) in configuration:")
        for error in sorted(v.iter_errors(config), key=str):
            print(error)
    else:
        print("config ok")


def main():
    sys.path.append(os.path.join(sys.path[0], 'lib'))
    schema = json.load(file(os.path.join(sys.path[0], "config_schema.json")))
    config = sys.argv[1] or os.path.join(sys.path[0], "config.yml")

    if os.path.exists(config):
        config = yaml.load(file(config))
    else:
        print("No config file found, please edit example.yml and rename it to config.yml")
        sys.exit(1)

    validate_config(config, schema)

    init_logging(config.get('logging', {}))

    factory = PyFiBotFactory(config)
    for network, settings in config['networks'].items():
        # settings = per network, config = global
        nick = settings.get('nick', None) or config['nick']
        linerate = settings.get('linerate', None) or config.get('linerate', None)
        password = settings.get('password', None)
        is_ssl = bool(settings.get('is_ssl', False))
        port = int(settings.get('port', 6667))

        # normalize channel names to prevent internal confusion
        chanlist = []
        for channel in settings['channels']:
            if channel[0] not in '&#!+':
                channel = '#' + channel
            chanlist.append(channel)

        server_name = settings['server']

        factory.createNetwork((server_name, port), network, nick, chanlist, linerate, password, is_ssl)
        if is_ssl:
            log.info("connecting via SSL to %s:%d" % (server_name, port))
            reactor.connectSSL(server_name, port, factory, ssl.ClientContextFactory())
        else:
            log.info("connecting to %s:%d" % (server_name, port))
            reactor.connectTCP(server_name, port, factory)
    reactor.run()

if __name__ == '__main__':
    main()
