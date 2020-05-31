# -*- coding: utf-8 -*-
# pylint: disable=unused-variable,no-member

"""
Bot core

@author Riku 'Shrike' Lindblad (shrike@addiktit.net)
@copyright Copyright (c) 2004 Riku Lindblad
@license New-Style BSD

"""

from __future__ import print_function, division

# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, threads
from twisted.python import rebuild

from types import FunctionType

import inspect
import string
import logging
import requests
from util import pyfiurl

# line splitting
import textwrap

__pychecker__ = "unusednames=i, classattr"

log = logging.getLogger("bot")


class CoreCommands(object):
    def command_echo(self, user, channel, args):
        self.say(channel, "%s: %s" % (user, args))

    def command_ping(self, user, channel, args):
        self.say(
            channel,
            "%s: My current ping is %.0fms"
            % (self.get_nick(user), self.pingAve * 100.0),
        )

    def command_rehash(self, user, channel, args):
        """Reload modules and optionally the configuration file. Usage: rehash [conf]"""

        if self.factory.isAdmin(user):
            try:
                # rebuild core & update
                log.info("rebuilding %r" % self)
                rebuild.updateInstance(self)

                # reload config file
                if args == "conf":
                    self.factory.reload_config()
                    self.say(channel, "Configuration reloaded.")

                # unload removed modules
                self.factory._unload_removed_modules()
                # reload modules
                self.factory._loadmodules()
            except Exception as e:
                self.say(channel, "Rehash error: %s" % e)
                log.error("Rehash error: %s" % e)
            else:
                self.say(channel, "Rehash OK")
                log.info("Rehash OK")

    def say(self, channel, message, length=None):
        """Must be implemented by the inheriting class"""
        raise NotImplementedError

    def command_join(self, user, channel, args):
        """Usage: join <channel>[@network] [password] - Join the specified channel"""

        if not self.factory.isAdmin(user):
            return

        password = None
        # see if we have multiple arguments
        try:
            args, password = args.split(" ", 1)
        except ValueError:
            pass

        # see if the user specified a network
        try:
            newchannel, network = args.split("@", 1)
        except ValueError:
            newchannel, network = args, self.network.alias

        try:
            bot = self.factory.allBots[network]
        except KeyError:
            self.say(channel, "I am not on that network.")
        else:
            log.debug("Attempting to join channel %s on ",
                      (newchannel, network))
            if newchannel in bot.network.channels:
                self.say(channel, "I am already in %s on %s." %
                         (newchannel, network))
                log.debug("Already on channel %s" % channel)
                log.debug("Channels I'm on this network: %s" %
                          bot.network.channels)
            else:
                if password:
                    bot.join(newchannel, key=password)
                    log.debug("Joined with password")
                else:
                    bot.join(newchannel)
                    log.debug("Joined")

    # alias of part
    def command_leave(self, user, channel, args):
        """Usage: leave <channel>[@network] - Leave the specified channel"""
        self.command_part(user, channel, args)

    def command_part(self, user, channel, args):
        """Usage: part <channel>[@network] - Leave the specified channel"""

        if not self.factory.isAdmin(user):
            return

        # part what and where?
        try:
            newchannel, network = args.split("@", 1)
        except ValueError:
            newchannel, network = args, self.network.alias

        # get the bot instance for this chat network
        try:
            bot = self.factory.allBots[network]
        except KeyError:
            self.say(channel, "I am not on that network.")
        else:
            # no arguments, attempt to part current channel
            if not newchannel:
                log.debug("Parted channel %s" % channel)
                bot.network.channels.remove(channel)
                bot.part(channel)
                return

            if newchannel in bot.network.channels:
                log.debug("Parted channel %s" % newchannel)
                bot.network.channels.remove(newchannel)
                bot.part(newchannel)
            else:
                log.debug(
                    "Attempted to part channel I am not on: %s@%s"
                    % (newchannel, network)
                )
                log.debug("Channels on network: %s" % bot.network.channels)

    def command_quit(self, user, channel, args):
        """Usage: logoff - Leave this network"""

        if not self.factory.isAdmin(user):
            return

        self.quit("Working as programmed")
        self.hasQuit = 1

    def command_channels(self, user, channel, args):
        """Usage: channels <network> - List channels the bot is on"""
        if not args:
            self.say(
                channel,
                "Please specify a network: %s" % ", ".join(
                    self.factory.allBots.keys()),
            )
            return

        self.say(channel, "I am on %s" % self.network.channels)

    def command_help(self, user, channel, cmnd):
        """Get help on all commands or a specific one. Usage: help [<command>]"""

        commands, admin_commands = [], []
        for module, env in self.factory.ns.items():
            myglobals, mylocals = env
            commands += [
                (c.replace("command_", ""), ref)
                for c, ref in mylocals.items()
                if c.startswith("command_%s" % cmnd)
            ]
            admin_commands += [
                (c.replace("admin_", ""), ref)
                for c, ref in mylocals.items()
                if c.startswith("admin_%s" % cmnd)
            ]
        # Help for a specific command
        if len(cmnd) > 0:
            for cname, ref in commands:
                if cname == cmnd:
                    helptext = ref.__doc__.split("\n", 1)[0]
                    self.say(channel, "Help for %s: %s" % (cmnd, helptext))
                    return
        # Generic help
        else:
            commandlist = ", ".join([c for c, ref in commands])
            admin_commandlist = ", ".join([c for c, ref in admin_commands])
            self.say(channel, "Available commands: %s" % commandlist)
            if self.factory.isAdmin(user):
                self.say(channel, "Available admin commands: %s" %
                         admin_commandlist)


class PyFiBot(irc.IRCClient, CoreCommands):
    """PyFiBot"""

    nickname = "pyfibot"
    realname = "https://github.com/lepinkainen/pyfibot"
    password = None

    # send 2 msgs per second max
    lineRate = 0.5
    hasQuit = False

    # Rolling ping time average
    pingAve = 0.0

    def __init__(self, config, network):
        self.cmdchar = config.get("cmdchar", ".")
        self.network = network
        self.nickname = self.network.nickname
        self.realname = self.network.realname or self.realname
        self.lineRate = self.network.linerate
        self.password = self.network.password
        # Text wrapper to clip overly long answers
        self.tw = textwrap.TextWrapper(width=400, break_long_words=True)
        log.info("bot initialized")

    def __repr__(self):
        return "PyFiBot(%r, %r)" % (self.nickname, self.network.address)

    # Core
    def printResult(self, msg, info):
        # Don't print results if there is nothing to say (usually non-operation on module)
        if msg:
            log.debug("Result %s %s" % (msg, info))

    def printError(self, msg, info):
        log.error("ERROR %s %s" % (msg, info))

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        self.repeatingPing(300)
        log.info("connection made")

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        log.info("connection lost: %s", reason)

    def signedOn(self):
        """Called when bot has succesfully connected to a server."""
        log.info("Connected to network")

        network_conf = self.factory.config["networks"][self.network.alias]

        # Name used for authentication
        authname = network_conf.get("authname", None)
        # Pass used for authentication
        authpass = network_conf.get("authpass", None)

        # If authentication is used
        if authname and authpass:
            # QuakeNet specific auth and IP-address masking
            if self.network.alias.lower() == "quakenet":
                log.info("I'm on Quakenet, authenticating...")
                self.mode(self.nickname, "+", "x")  # Hide ident
                log.info("Authenticating...")
                self.say("Q@CServe.quakenet.org", "AUTH %s %s" %
                         (authname, authpass))
            # more generic authentication
            else:
                # Get authentication service
                # Default: None
                # None as default, so the user must be sure who he's authenticating to
                authservice = network_conf.get("authservice", None)
                if authservice:
                    # Command used for authentication
                    # Default: "IDENTIFY authname authpass"
                    authcommand = network_conf.get(
                        "authcommand", "IDENTIFY %(authname)s %(authpass)s"
                    )
                    authcommand = authcommand % {
                        "authname": authname,
                        "authpass": authpass,
                    }

                    log.info('Authenticating to "%s"' % authservice)
                    log.debug('Authentication command used: "%s"' %
                              authcommand)
                    self.say(authservice, authcommand)
                else:
                    log.info("authservice not set, authentication not attempted")
        else:
            log.debug(
                "authname or authpass not found, authentication not attempted")

        authdelay = network_conf.get("authdelay", None)
        if authdelay:
            # allowing the connection to establish and authentication to happen before joining
            log.info("Joining channels after %s second delay" % (authdelay))
            reactor.callLater(authdelay, self.joinChannels)
        else:
            self.joinChannels()

    # separate function to allow timing the joins
    def joinChannels(self):
        for chan in self.network.channels:
            # Defined as a tuple, channel has a key
            if type(chan) == list:
                self.join(chan[0], key=chan[1])
            else:
                self.join(chan)

        log.info(
            "joined %d channel(s): %s"
            % (len(self.network.channels), ", ".join(self.network.channels))
        )
        self._runEvents("signedon")

    def pong(self, user, secs):
        self.pingAve = ((self.pingAve * 5) + secs) / 6.0

    def repeatingPing(self, delay):
        reactor.callLater(delay, self.repeatingPing, delay)
        self.ping(self.nickname)

    # TODO: Move the function here completely
    def get_url(self, url, nocache=False, params=None, headers=None, cookies=None):
        browser = "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:49.0) Gecko/20100101 Firefox/49.0"
        # Common session for all requests
        s = requests.session()
        s.stream = True  # Don't fetch content unless asked
        s.headers.update({"User-Agent": browser})
        s.headers.update({"Accept-Language": "*"})
        s.headers.update(
            {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"})
        # Custom headers from requester
        if headers:
            s.headers.update(headers)
        # Custom cookies from requester
        if cookies:
            s.cookies.update(cookies)

        try:
            r = s.get(url, params=params, timeout=5)
        except requests.exceptions.InvalidSchema:
            log.error("Invalid schema in URI: %s" % url)
            return None
        except requests.exceptions.SSLError:
            log.error("SSL Error when connecting to %s" % url)
            return None
        except requests.exceptions.ConnectionError:
            log.error("Connection error when connecting to %s" % url)
            return None

        size = int(r.headers.get("Content-Length", 0)) // 1024
        size = size / 1024 / 1024  # Size in MB

        content_type = r.headers.get("content-type", None)
        if not content_type:
            content_type = "Unknown"

        if size > 5:
            bot.say(channel, "File size: %s MB - Content-Type: %s" %
                    (int(size), content_type))

        if size > 2:
            log.warn("Content too large, will not fetch: %skB %s" %
                     (size, url))
            return None

        return r

    def getUrl(self, url, nocache=False, params=None, headers=None, cookies=None):
        return self.get_url(url, nocache, params, headers, cookies)

    def isAdmin(self, user):
        return self.factory.isAdmin(user)

    def is_admin(self, user):
        return self.factory.isAdmin(user)

    def get_nick(self, user):
        return self.getNick(user)

    def getNick(self, user):
        """Parses nick from nick!user@host
        @type user: string
        @param user: nick!user@host
        @return: nick"""
        return user.split("!", 1)[0]

    def log(self, message):
        botId = "%s@%s" % (self.nickname, self.network.alias)
        log.info("%s: %s", botId, message)

    def callLater(self, delay, callable):
        self.callLater(delay, callable)

    # Communication
    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message.
        @param user: nick!user@host
        @param channel: Channel where the message originated from
        @param msg: The actual message
        """

        channel = channel.lower()
        lmsg = msg.lower()
        lnick = self.nickname.lower()
        nickl = len(lnick)
        if channel == lnick:
            # Turn private queries into a format we can understand
            if not msg.startswith(self.cmdchar):
                msg = self.cmdchar + msg
            elif lmsg.startswith(lnick):
                msg = self.cmdchar + msg[nickl:].lstrip()
            elif (
                lmsg.startswith(lnick)
                and len(lmsg) > nickl
                and lmsg[nickl] in string.punctuation
            ):
                msg = self.cmdchar + msg[nickl + 1:].lstrip()
        else:
            # Turn 'nick:' prefixes into self.cmdchar prefixes
            if (
                lmsg.startswith(lnick)
                and len(lmsg) > nickl
                and lmsg[nickl] in string.punctuation
            ):
                msg = self.cmdchar + msg[len(self.nickname) + 1:].lstrip()
        reply = (channel == lnick) and user or channel

        if msg.startswith(self.cmdchar):
            cmnd = msg[len(self.cmdchar):]
            self._command(user, reply, cmnd)

        # Run privmsg handlers
        self._runhandler("privmsg", user, reply, self.factory.to_unicode(msg))

        # run URL handlers
        urls = pyfiurl.grab(msg)
        if urls:
            for url in urls:
                self._runhandler("url", user, reply, url,
                                 self.factory.to_unicode(msg))

    def _runhandler(self, handler, *args, **kwargs):
        """Run a handler for an event"""
        handler = "handle_%s" % handler
        # module commands
        for module, env in self.factory.ns.items():
            myglobals, mylocals = env
            # find all matching command functions
            handlers = [
                (h, ref)
                for h, ref in mylocals.items()
                if h == handler and type(ref) == FunctionType
            ]

            for hname, func in handlers:
                # defer each handler to a separate thread, assign callbacks to see when they end
                d = threads.deferToThread(func, self, *args, **kwargs)
                d.addCallback(self.printResult, "handler %s completed" % hname)
                d.addErrback(self.printError, "handler %s error" % hname)

    def _runEvents(self, eventname, *args, **kwargs):
        """Run funtions on events named by eventname parameter"""
        eventname = "event_%s" % eventname
        for module, env in self.factory.ns.items():
            myglobals, mylocals = env

            # find all matching events
            events = [
                (h, ref)
                for h, ref in mylocals.items()
                if h == eventname and type(ref) == FunctionType
            ]

            for ename, func in events:
                # defer each handler to a separate thread, assign callbacks to see when they end
                d = threads.deferToThread(func, self, *args, **kwargs)
                d.addCallback(
                    self.printResult, "%s %s event completed" % (module, ename)
                )
                d.addErrback(self.printError, "%s %s event error" %
                             (module, ename))

    def _command(self, user, channel, cmnd):
        """Handles bot commands.

        This function calls the appropriate method for the given command.

        The command methods are formatted as "command_<commandname>"
        """
        # Split arguments from the command part
        try:
            cmnd, args = cmnd.split(" ", 1)
        except ValueError:
            args = ""

        # core commands
        method = getattr(self, "command_%s" % cmnd, None)
        if method is not None:
            log.info(
                "internal command %s called by %s (%s) on %s"
                % (cmnd, user, self.factory.isAdmin(user), channel)
            )
            method(user, channel, args)
            return

        # module commands
        for module, env in self.factory.ns.items():
            myglobals, mylocals = env
            # find all matching command functions
            commands = [
                (c, ref) for c, ref in mylocals.items() if c == "command_%s" % cmnd
            ]
            commands += [
                (c, ref) for c, ref in mylocals.items() if c == "admin_%s" % cmnd
            ]

            for cname, command in commands:
                if not self.factory.isAdmin(user) and cname.startswith("admin"):
                    continue
                i = inspect.getcallargs(command, self, user, channel, cmnd)
                if "silent" not in i:
                    log.info(
                        "module command %s called by %s (%s) on %s"
                        % (cname, user, self.factory.isAdmin(user), channel)
                    )
                # Defer commands to threads
                d = threads.deferToThread(
                    command, self, user, channel, self.factory.to_unicode(
                        args.strip())
                )
                d.addCallback(self.printResult, "command %s completed" % cname)
                d.addErrback(self.printError, "command %s error" % cname)

    # Overrides for twisted.words.irc core commands #
    def say(self, channel, message, length=None):
        """Override default say to make replying to private messages easier"""

        # Encode channel
        # (for cases where channel is specified in code instead of "answering")
        channel = self.factory.to_utf8(channel)
        # Encode all outgoing messages to UTF-8
        message = self.factory.to_utf8(message)

        # Change nick!user@host -> nick, since all servers don't support full hostmask messaging
        if "!" and "@" in channel:
            channel = self.get_gick(channel)

        # wrap long text into suitable fragments
        msg = self.tw.wrap(message)
        cont = False

        for m in msg:
            if cont:
                m = "..." + m
            self.msg(channel, m, length)
            cont = True

        return ("botcore.say", channel, message)

    def act(self, channel, message, length=None):
        """Use act instead of describe for actions"""
        return super(PyFiBot, self).describe(channel, message)

    def mode(self, chan, set, modes, limit=None, user=None, mask=None):
        chan = self.factory.to_utf8(chan)
        _set = self.factory.to_utf8(set)
        modes = self.factory.to_utf8(modes)
        return super(PyFiBot, self).mode(chan, _set, modes, limit, user, mask)

    def kick(self, channel, user, reason=None):
        reason = self.factory.to_utf8(reason)
        return super(PyFiBot, self).kick(channel, user, reason)

    def join(self, channel, key=None):
        channel = self.factory.to_utf8(channel)
        return super(PyFiBot, self).join(channel, key)

    def leave(self, channel, key=None):
        channel = self.factory.to_utf8(channel)
        return super(PyFiBot, self).leave(channel, key)

    def quit(self, message=""):
        message = self.factory.to_utf8(message)
        return super(PyFiBot, self).quit(message)

    # Overrides for twisted.words.irc internal commands #
    def XXregister(self, nickname, hostname="foo", servername="bar"):
        nickname = self.factory.to_utf8(nickname)
        hostname = self.factory.to_utf8(hostname)
        servername = self.factory.to_utf8(servername)
        return super(PyFiBot, self).register(nickname, hostname, servername)

        # self.sendLine("USER %s %s %s :%s" % (self.username, hostname, servername, self.realname))
        # self.register(nickname, hostname, servername)

    # LOW-LEVEL IRC HANDLERS #

    def irc_JOIN(self, prefix, params):
        """override the twisted version to preserve full userhost info"""
        nick = self.get_nick(prefix)
        channel = params[-1]

        if nick == self.nickname:
            self.joined(channel)
        else:
            self.userJoined(prefix, channel)

        if nick.lower() != self.nickname.lower():
            pass
        elif channel not in self.network.channels:
            self.network.channels.append(channel)
            self.factory.setNetwork(self.network)

    def irc_PART(self, prefix, params):
        """override the twisted version to preserve full userhost info"""

        nick = self.get_nick(prefix)
        channel = params[0]

        if nick == self.nickname:
            self.left(channel)
        else:
            # some clients don't send a part message at all, compensate
            if len(params) == 1:
                params.append("")
            self.userLeft(prefix, channel, params[1])

    def irc_NICK(self, prefix, params):
        """override the twisted version to preserve full userhost info"""
        newnick = params[0]
        self.userRenamed(prefix, newnick)

    def irc_QUIT(self, prefix, params):
        """QUIT-handler.

        Twisted IRCClient doesn't handle this at all.."""

        nick = self.get_nick(prefix)
        if nick == self.nickname:
            self.left(params)
        else:
            self.userLeft(prefix, None, params[0])

    # HANDLERS #

    # ME #
    def joined(self, channel):
        """I joined a channel"""
        self._runhandler("joined", channel)

    def left(self, channel):
        """I left a channel"""
        self._runhandler("left", channel)

    def noticed(self, user, channel, message):
        """I received a notice"""
        self._runhandler("noticed", user, channel,
                         self.factory.to_unicode(message))

    def modeChanged(self, user, channel, set, modes, args):
        """Mode changed on user or channel"""
        self._runhandler("modeChanged", user, channel, set, modes, args)

    def kickedFrom(self, channel, kicker, message):
        """I was kicked from a channel"""
        self._runhandler(
            "kickedFrom", channel, kicker, self.factory.to_unicode(message)
        )

    def nickChanged(self, nick):
        """I changed my nick"""
        self._runhandler("nickChanged", nick)

    # OTHER PEOPLE
    def userJoined(self, user, channel):
        """Someone joined"""
        self._runhandler("userJoined", user, channel)

    def userLeft(self, user, channel, message):
        """Someone left"""
        self._runhandler("userLeft", user, channel,
                         self.factory.to_unicode(message))

    def userKicked(self, kickee, channel, kicker, message):
        """Someone got kicked by someone"""
        self._runhandler(
            "userKicked", kickee, channel, kicker, self.factory.to_unicode(
                message)
        )

    def action(self, user, channel, data):
        """An action"""
        self._runhandler("action", user, channel,
                         self.factory.to_unicode(data))

    def topicUpdated(self, user, channel, topic):
        """Save topic to maindb when it changes"""
        self._runhandler("topicUpdated", user, channel,
                         self.factory.to_unicode(topic))

    def userRenamed(self, oldnick, newnick):
        """Someone changed their nick"""
        self._runhandler("userRenamed", oldnick, newnick)

    def receivedMOTD(self, motd):
        """MOTD"""
        self._runhandler("receivedMOTD", self.factory.to_unicode(motd))

    # SERVER INFORMATION

    # Network = Quakenet -> do Q auth
    def isupport(self, options):
        log.info(self.network.alias + " SUPPORTS: " + ",".join(options))

    def created(self, when):
        log.info(self.network.alias + " CREATED: " + when)

    def yourHost(self, info):
        log.info(self.network.alias + " YOURHOST: " + info)

    def myInfo(self, servername, version, umodes, cmodes):
        log.info(
            self.network.alias
            + " MYINFO: %s %s %s %s" % (servername, version, umodes, cmodes)
        )

    def luserMe(self, info):
        log.info(self.network.alias + " LUSERME: " + info)
