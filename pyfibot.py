#!/usr/bin/python

"""A modular python bot based on the twisted matrix irc library

@author Riku 'Shrike' Lindblad (shrike@addiktit.net)
@copyright Copyright (c) 2006 Riku Lindblad
@license BSD
"""

try:
    import psyco
    psyco.full()
except ImportError:
    print "Psyco not found, running unoptimized"

# twisted imports
from twisted.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log, rebuild

# system imports
#import shelve
import sys
import os.path
import time
import urllib
import fnmatch

from util import *
from util.BeautifulSoup import BeautifulSoup

# bot core
import botcore

class URLCacheItem(object):
    """URL cache item object, fetches data only when needed"""
    
    def __init__(self, url):
        self.url = url
        self.content = None
        self.headers = None
        self.bs = None
        # maximum size in kB to download
        self.max_size = 2048
        self.fp = None

    def _open(self, url):
        """Returns the raw file pointer to the given URL"""
        if not self.fp:
            urllib._urlopener = BotURLOpener()
            self.fp = urllib.urlopen(self.url)
        return self.fp

    def _checkstatus(self):
        """Check if all data has already been cached and close socket if so"""
        
        if self.content and \
           self.headers and \
           self.bs:
            self.fp.close()

    def getSize(self):
        """Get the content length of URL in kB

        @return None if the server doesn't return a content-length header"""
        if self.getHeaders().has_key('content-length'):
            length = int(self.getHeaders()['content-length'])/1024
            return length
        else:
            return None

    def getContent(self):
        """Get the actual file at the URL

        @return None if the file is too large (over 2MB)"""
        if not self.content:
            f = self._open(self.url)

            size = self.getSize()
            if size > self.max_size:
                print "CONTENT TOO LARGE, WILL NOT FETCH", size, self.url
                self.content = None
            else:
                self.content = f.read()

        self._checkstatus()
        return self.content

    def getHeaders(self):
        """Get headers for the URL"""
        
        if not self.headers:
            f = self._open(self.url)
            self.headers = f.info()
        
        self._checkstatus()
        return self.headers

    def getBS(self):
        """Get a beautifulsoup instance for the URL

        @return None if the url doesn't contain HTML
        """
        
        if not self.bs:
            # only attempt a bs parsing if the content is html or xhtml
            if self.getHeaders().has_key('content-type') and \
            self.getHeaders().getsubtype() == 'html' or \
            self.getHeaders().getsubtype() == 'xhtml+xml':
            
                bs = BeautifulSoup()
                bs.feed(self.getContent())
                self.bs = bs
            else:
                #print "NOT HTML, NO BS", self.url
                return None
            
        self._checkstatus()
        return self.bs

class BotURLOpener(urllib.FancyURLopener):
    """Url opener that fakes itself as Firefox and ignores all basic auth prompts"""
    
    def __init__(self, *args):
        # Firefox 1.0PR on w2k
        self.version = "Mozilla/5.0 (Windows; U; Windows NT 5.0; rv:1.7.3) PyFiBot"
        urllib.FancyURLopener.__init__(self, *args)

    def prompt_user_passwd(self, host, realm):
        print "PASSWORD PROMPT:", host, realm
        return ('', '')

class Network:
    def __init__(self, root, alias, address, nickname, channels = None):
        self.alias = alias                         # network name
        self.address = address                     # server address
        self.nickname = nickname                   # nick to use
        self.channels = channels or {}             # channels to join

        # create network specific save directory
        p = os.path.join(root, alias)
        if not os.path.isdir(p):
            os.mkdir(p)

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
        print connector
        print "connection lost (%s): reconnecting in %d seconds" % (reason, self.lostDelay)
        reactor.callLater(self.lostDelay, connector.connect)
        
    def clientConnectionFailed(self, connector, reason):
        print connector
        print "connection failed (%s): reconnecting in %d seconds" % (reason, self.failedDelay)
        reactor.callLater(self.failedDelay, connector.connect)
                                                                        
class PyFiBotFactory(ThrottledClientFactory):
    """python.fi bot factory"""

    admins = [
        '*!shrike@a84-231-111-13.elisa-laajakaista.fi',
        '*!shrike@sunshine.sjr.fi',
        '*!shrike@ipv6.sjr.fi',
        '*!shrike@hpsjr.fi',
        '*!shrike@tefra.fi',
        ]

    version = "$Revision$"

    protocol = botcore.PyFiBot
    allBots = None
    
    moduledir = "modules/"

    startTime = None

    def __init__(self, db):
        """Initialize the factory"""

        self.data = db
        self.data['networks'] = {}
        self.ns = {}

        # cache url contents for 10 minutes, check for old entries every minute
        self._urlcache = timeoutdict.TimeoutDict(timeout=600, pollinterval=60)

        if not os.path.exists("data"):
            os.mkdir("data")
                        
    def startFactory(self):
        self.allBots = {}
        self.starttime = time.time()

        self._loadmodules()

        ThrottledClientFactory.startFactory(self)

        self.log("factory started")

    def stopFactory(self):

        del self.allBots
        #self.data.close()
        
        ThrottledClientFactory.stopFactory(self)
        self.log("factory stopped")
        
    def buildProtocol(self, address):
        address = (address.host, address.port)

        # do we know how to connect to the given address?
        for n in self.data['networks'].values():
            if n.address == address:
                break
        else:
            self.log("unknown network address: " + repr(address))
            return InstantDisconnectProtocol()

        p = self.protocol(n)
        self.allBots[n.alias] = p
        p.factory = self
        return p

    def createNetwork(self, address, alias, nickname, channels = None):
        self.setNetwork(Network("data", alias, address, nickname, channels))
                
    def setNetwork(self, net):
        nets = self.data['networks']
        nets[net.alias] = net
        self.data['networks'] = nets

    def clientConnectionLost(self, connector, reason):
        """Connection lost for some reason"""
        self.log("connection to %s lost" % str(connector.getDestination().host))

        # find bot that connects to the address that just disconnected
        for n in self.data['networks'].values():
            dest = connector.getDestination()
            #print "DESTINATION: "+str(dest)
            if (dest.host, dest.port) == n.address:
                if self.allBots.has_key(n.alias):
                    # did we quit intentionally?
                    if not self.allBots[n.alias].hasQuit:
                        # nope, reconnect
                        ThrottledClientFactory.clientConnectionLost(self, connector, reason)
                    del self.allBots[n.alias]
                    return
                else:
                    self.log("No active connection to known network %s" % n.address)

    def _finalize_modules(self):
        """Call all module finalizers"""
        for module in self._findmodules():
            # if rehashing (module already in namespace), finalize the old instance first
            if self.ns.has_key(module):
                if self.ns[module][0].has_key('finalize'):
                    self.log("finalize - %s" % module)
                    self.ns[module][0]['finalize']()


    def _loadmodules(self):
        """Load all modules"""
        self._finalize_modules()
        
        for module in self._findmodules():

            env = self._getGlobals()
            self.log("load module - %s" % module)
            # Load new version of the module
            execfile(os.path.join(self.moduledir, module), env, env)
            # initialize module
            if env.has_key('init'):
                self.log("initialize module - %s" % module)
                env['init']()
            
            # add to namespace so we can find it later
            self.ns[module] = (env, env)

    def _findmodules(self):
        """Find all modules"""
        modules = [m for m in os.listdir(self.moduledir) if m.startswith("module_") and m.endswith(".py")]
        return modules

    def _runhandler(self, handler, *args, **kwargs):
        """Run a handler for an event"""
        handler = "handle_%s" % handler
        # module commands
        for module, env in self.ns.items():
            myglobals, mylocals = env
            # find all matching command functions
            handlers = [(h,ref) for h,ref in mylocals.items() if h == handler and type(ref) == FunctionType]

            for hname, func in handlers:
                func(*args, **kwargs)

    def _getGlobals(self):
        """Global methods for modules"""
        g = {}

        g['getUrl'] = self.getUrl
        g['getNick'] = self.getNick
        g['isAdmin'] = self.isAdmin
        return g

    def getUrl(self, url, nocache=False):
        """Gets data, bs and headers for the given url, using the internal cache if necessary"""
        
        if self._urlcache.has_key(url) and not nocache:
            self.log("internal cache hit: %s" % url)
        else:
            if nocache:
                self.log("cache pass: %s" % url)
            else:
                self.log("cache miss: %s" % url)
            self._urlcache[url] = URLCacheItem(url)
            
        return self._urlcache[url]

    def getNick(self, user):
        """Parses nick from nick!user@host
        
        @type user: string
        @param user: nick!user@host
        
        @return: nick"""
        return user.split('!', 1)[0]

    def isAdmin(self, user):
        """Check if an user has admin privileges.
        
        @return: True or False"""
    
        for pattern in self.admins:
            if fnmatch.fnmatch(user, pattern):
                return True
        
        return False

    def log(self, message):
        print "%-20s: %s" % ("core", message)
                                                                                                                                    
if __name__ == '__main__':

    sys.path.append(os.path.join(sys.path[0], 'lib'))

    #db = shelve.open("pyfibot.shelve")
    db = {}
    f = PyFiBotFactory(db)
    #f.createNetwork(("irc.kolumbus.fi", 6667), "ircnet", "pyfibot", ["#pyfitest"])
    f.createNetwork(("irc.inet.fi", 6667), "ircnet", "pyfibot", ["#ioh9s1", "#soukka.net", "#python.fi", "#norsu", "#yomi"])
    f.createNetwork(("efnet.xs4all.nl", 6667), "efnet", "pyfibot", [("#ankkalinna","millamagia")])
    f.createNetwork(("mediatraffic.fi.quakenet.org", 6667), "quakenet", "pyfibot", ["#k21", "#northernprime"])
    reactor.connectTCP("irc.inet.fi", 6667, f)
    #reactor.connectTCP("efnet.xs4all.nl", 6667, f)
    reactor.connectTCP("mediatraffic.fi.quakenet.org", 6667, f)
    
    reactor.run()

