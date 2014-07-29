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
from copy import deepcopy

import colorlogger
USE_COLOR = True

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
from util.dictdiffer import DictDiffer

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

        # No address found
        log.error("Unknown network address: " + repr(address))
        return InstantDisconnectProtocol()

    def createNetwork(self, address, alias, nickname, channels=None, linerate=None, password=None, is_ssl=False):
        self.setNetwork(Network("data", alias, address, nickname, channels, linerate, password, is_ssl))

    def setNetwork(self, net):
        self.data['networks'][net.alias] = net

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

    def _finalize_modules(self, modules=None):
        """Call all module finalizers"""
        if modules is None:
            modules = self._findmodules()
        for module in modules:
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

    def _unload_removed_modules(self):
        """Unload modules removed from modules -directory"""
        # find all modules in namespace, which aren't present in modules -directory
        removed_modules = [m for m in self.ns if not m in self._findmodules()]
        self._finalize_modules(removed_modules)

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
        g['getIdent'] = self.getIdent
        g['getHost'] = self.getHost
        g['isAdmin'] = self.isAdmin
        g['to_utf8'] = self.to_utf8
        g['to_unicode'] = self.to_unicode
        return g

    def get_url(self, url, nocache=False, params=None, headers=None, cookies=None):
        return self.getUrl(url, nocache, params, headers, cookies)

    def getUrl(self, url, nocache=False, params=None, headers=None, cookies=None):
        """Gets data, bs and headers for the given url, using the internal cache if necessary"""

        browser = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.95 Safari/537.11"
        # Common session for all requests
        s = requests.session()
        s.verify = False
        s.stream = True  # Don't fetch content unless asked
        s.headers.update({'User-Agent': browser})
        # Custom headers from requester
        if headers:
            s.headers.update(headers)
        # Custom cookies from requester
        if cookies:
            s.cookies.update(cookies)

        try:
            r = s.get(url, params=params)
        except requests.exceptions.InvalidSchema:
            log.error("Invalid schema in URI: %s" % url)
            return None
        except requests.exceptions.ConnectionError:
            log.error("Connection error when connecting to %s" % url)
            return None

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

    def getIdent(self, user):
        """Parses ident from nick!user@host
        @type user: string
        @param user: nick!user@host
        @return: ident"""
        return user.split('!', 1)[1].split('@')[0]

    def getHost(self, user):
        """Parses host from nick!user@host
        @type user: string
        @param user: nick!user@host
        @return: host"""
        return user.split('@', 1)[1]

    def isAdmin(self, user):
        """Check if an user has admin privileges.
        @return: True or False"""
        for pattern in self.config['admins']:
            if fnmatch.fnmatch(user, pattern):
                return True
        return False

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

    def reload_config(self):
        """Reload config-file while bot is running (on rehash)"""
        log = logging.getLogger('reload_config')

        config = read_config()
        if not config:
            return

        valid_config = validate_config(config)
        if not valid_config:
            log.info('Invalid config file!')
            return

        log.info('Valid config file found, reloading...')
        # ignore nick and networks, as we don't want rehash to change these values
        ignored = ['nick', 'networks']
        # make a deep copy of old config, so we don't remove values from it
        old_config = deepcopy(self.config)
        # remove ignored values to make comparing/updating easier and safer
        for k in ignored:
            old_config.pop(k, {})
            config.pop(k, {})

        # Get diff between configs
        dd = DictDiffer(config, old_config)

        for k in dd.added():
            log.info('%s added (%s: %s' % (k, k, config[k]))
            self.config[k] = config[k]
        for k in dd.removed():
            log.info('%s removed (%s: %s)' % (k, k, old_config[k]))
            del self.config[k]
        for k in dd.changed():
            log.info('%s changed' % k)
            # compare configs
            d = DictDiffer(config[k], old_config[k])
            # add all changes to a big list
            changes = list(d.added())
            changes.extend(list(d.removed()))
            changes.extend(list(d.changed()))
            # loop through changes and log them individually
            for x in changes:
                log.info('%s[\'%s\']: \'%s\' -> \'%s\'' % (k, x, old_config[k].get(x, {}), config[k].get(x, {})))
            # replace the whole object
            self.config[k] = config[k]

        # change logging level, default to INFO
        log_level = config.get('logging', {}).get('debug', False)
        if log_level:
            logging.root.setLevel(logging.DEBUG)
        else:
            logging.root.setLevel(logging.INFO)

    def find_bot_for_network(self, network):
        if network not in self.allBots:
            return None
        return self.allBots[network]


def init_logging(config):
    logger = logging.getLogger()

    if config.get('debug', False):
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    if USE_COLOR:
        FORMAT = "[%(asctime)-15s][%(levelname)-20s][$BOLD%(name)-15s$RESET]  %(message)s"
        # Append file name + number if debug is enabled
        if config.get('debug', False):
            FORMAT = "%s %s" % (FORMAT, " ($BOLD%(filename)s$RESET:%(lineno)d)")
        COLOR_FORMAT = colorlogger.formatter_message(FORMAT, True)
        formatter = colorlogger.ColoredFormatter(COLOR_FORMAT)
    else:
        FORMAT = "%(asctime)-15s %(levelname)-8s %(name)-11s %(message)s"
        formatter = logging.Formatter(FORMAT)
        # Append file name + number if debug is enabled
        if config.get('debug', False):
            FORMAT = "%s %s" % (FORMAT, " (%(filename)s:%(lineno)d)")

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def read_config():
    config_file = sys.argv[1] or os.path.join(sys.path[0], "config.yml")

    if os.path.exists(config_file):
        config = yaml.load(file(config_file))
    else:
        print("No config file found, please edit example.yml and rename it to config.yml")
        return
    return config


def validate_config(config):
    schema = json.load(file(os.path.join(sys.path[0], "config_schema.json")))
    log.info("Validating configuration")
    v = jsonschema.Draft3Validator(schema)
    if not v.is_valid(config):
        log.error("Error(s) in configuration:")
        for error in sorted(v.iter_errors(config), key=str):
            log.error(error)
        return False
    log.info("Config ok")
    return True


def main():
    sys.path.append(os.path.join(sys.path[0], 'lib'))

    config = read_config()
    # if config not found or can't validate it, exit with error
    if not config or not validate_config(config):
        sys.exit(1)

    init_logging(config.get('logging', {}))

    factory = PyFiBotFactory(config)
    for network, settings in config['networks'].items():
        # settings = per network, config = global
        nick = settings.get('nick', None) or config['nick']
        linerate = settings.get('linerate', 0.5) or config.get('linerate', 0.5)
        password = settings.get('password', None)
        is_ssl = bool(settings.get('is_ssl', False))
        port = int(settings.get('port', 6667))
        force_ipv6 = bool(settings.get('force_ipv6', False))

        # normalize channel names to prevent internal confusion
        chanlist = []
        # allow bot to connect even if no channels are declared
        if 'channels' in settings:
            for channel in settings['channels']:
                if channel[0] not in '&#!+':
                    channel = '#' + channel
                chanlist.append(channel)
        else:
            log.warning('No channels defined for "%s"' % network)

        if force_ipv6:
            try:
                server_name = socket.getaddrinfo(settings['server'], port, socket.AF_INET6)[0][4][0]
            except IndexError:
                log.error('No IPv6 address found for %s (force_ipv6 = true)' % (network))
                continue
        else:
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
